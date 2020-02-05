import re
from os import path
from fnmatch import fnmatch # fnmatch(test_string, glob_pattern)
from typing import List
import database

RULE_REGEX = r'^(\S+)\s*(\S*)\s+〜(\S*)\s*(\S*)\s+for\s+(\S*)\s+〜(\S*) +((?:[ \t]*\S+)+)\s*$'

CURRENT_DIRECTORY = path.dirname(__file__)
RULES_FILENAME = path.join(CURRENT_DIRECTORY, 'grammar.rules')

VOWEL_KATAKANA = list("アイウエオ")
SOUND_CHANGE = {
    "": [""]*9,
    "ア": list("さかがまばならわた"),
    "イ": list("しきぎみびにりいち"),
    "ウ": list("すくぐむぶぬるうつ"),
    "エ": list("せけげめべねれえて"),
    "オ": list("そこごもぼのろおと")
}

class Rule:
    """
    Represents a grammar rule
    RULE      [ROLE] PATTERN [POS] for TARGET TARGET_PATTERN POS-GLOB...
    potential plain  〜エる  v1    for plain  〜ウ           v5[^r]* v5r vs-c
    """
    def __init__(self, rule: str, role: str, pattern: str, pos: str, target: str,
                 target_pattern: str, pos_globs: List[str]):
        assert type(pos_globs) is list
        self.rule = rule
        self.role = role
        self.pattern = pattern
        self.pos = pos
        self.traget = target
        self.target_pattern = target_pattern
        self.pos_globs = pos_globs
    def __str__(self):
        string = self.rule
        if self.role:
            string += " " + self.role
        string += " ~" + self.pattern
        if self.pos:
            string += " " + self.pos
        string += " for {} ~{} {}".format(self.traget, self.target_pattern, " ".join(self.pos_globs))
        return string
    def __repr__(self):
        return "{} {} ~{} {} for {} ~{} {}".format(self.rule, self.role, self.pattern, self.pos, self.traget, self.target_pattern, " ".join(self.pos_globs))

def parse_rules(filename=RULES_FILENAME):
    rules = []
    with open(filename, 'r', encoding='utf-8') as f:
        line_number = 0
        for line in f:
            line_number += 1
            if re.match(r'^\s*#.*$', line): # skip comment lines
                continue
            if re.match(r'^\s*$', line):    # skip empty lines
                continue
            line = re.sub(r'#.*', "", line) # remove comments
            match = re.match(RULE_REGEX, line)
            if not match:
                raise SyntaxError("Error parsing line {}: {}".format(line_number, line))
            rule, role, pattern, pos, target, target_pattern, pos_globs = match.groups()
            pos_globs = pos_globs.split()
            # role and pos are optional
            # pattern and target_pattern can be empty
            # rule, target and globs are required
            if "" in [rule, target] or len(pos_globs) <= 0:
                raise SyntaxError("Error parsing line {}: {}".format(line_number, line))
            role = None if role == "" else role
            pos = None if pos == "" else pos
            if len(pattern) <= 0 or pattern[0] not in VOWEL_KATAKANA:
                rules.append(Rule(rule, role, pattern, pos, target, target_pattern, pos_globs))
            else:
                # expansion required
                expansion_regex = r'^([アイウエオ]?).*$'
                sound = re.match(expansion_regex, pattern)[1]
                assert sound != "" # is guaranteed by previous if statement
                # sound_target can be empty
                sound_target = re.match(expansion_regex, target_pattern)[1]
                assert 9 == len(SOUND_CHANGE[sound]) == len(SOUND_CHANGE[sound_target])
                for i in range(9):
                    rules.append(Rule(rule, role,
                                      re.sub(expansion_regex, SOUND_CHANGE[sound][i], pattern),
                                      pos, target,
                                      re.sub(expansion_regex, SOUND_CHANGE[sound_target][i], target_pattern),
                                      pos_globs))
        return rules

def grammar_lookup(rules: List[Rule], expression: str, db:database.Database=None, tags: List[str] = ["*"], role: str = None, path: List = [], verbous=False):
    """
    Recursively looks up what form the expression is in
    Top level call: grammar_lookup(rules, expression)
    rules - list of grammar rules to use for lookup
    expression - a conjugated Japanese expression
    tags - list of glob patterns for possible tags of the expression
    role - grammatical role of the current expression (for example "plain", "past", or None = any role)
    path - holds the traversed path to the current expression
    """
    if len(path) <= 0:
        path = [(expression, " ".join(tags), role)]
    if verbous:
        print("{}({}, {}, {}):::::::::".format("\t" * (len(path)-1), expression, " ".join(tags), role))
    if len(path) > 20:
        raise RuntimeError("Possible recursion loop (limit reached)")
    # find applicable rules
    applicable = set()
    for rule in rules:
        if role not in [None, rule.rule, rule.role]:
            continue # skip rules with unmatching role
        if not expression.endswith(rule.pattern):
            continue # skip rules with unmatching pattern
        # take rules that contain a matching tag
        for tag in tags:
            # tag is a glob pattern
            if rule.pos and fnmatch(rule.pos, tag):
                applicable.add(rule)
                break
            elif not rule.pos:
                for pos in rule.pos_globs:
                    if fnmatch(pos, tag):
                        applicable.add(rule)
                        break
            else:
                pass # explicit, so that it is clear
    if len(applicable) == 0:
        if verbous:
            print("\t"*(len(path)-1) + "dead end")
        return None
    for rule in applicable:
        new_expression = expression[:len(expression)-len(rule.pattern)] + rule.target_pattern
        # this will be saved in the resulting path
        node_representation = (new_expression, " ".join(rule.pos_globs[:]), rule.rule)
        if verbous:
            print("\t"*len(path) + str(rule))
        if rule.traget == "plain":
            entry = db.find_exact(new_expression)
            if entry:
                return path + [node_representation], entry
        result = grammar_lookup(rules, new_expression, db, rule.pos_globs, rule.traget, path + [node_representation], verbous)
        if result:
            return result
    return None # can be shortened



if __name__ == "__main__":
    # for rule in parse_rules():
    #     print(repr(rule))
    rules = parse_rules()
    db = database.connect()
    # 書いてた
    path, entry = grammar_lookup(rules, "書いてた", db, verbous=True)
    for i in range(len(path) - 1):
        print("{}{} is {} for {}".format(" "*i, path[i][0], path[i+1][2], path[i+1][0]))
    print("Dictionary entry for: {} {}".format(path[-1][0], path[-1][1]))
    print(" ".join(entry["writings"]))
    print(" ".join(entry["readings"]))
    print(", ".join(entry["senses"][0]["glosses"]))
