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

def grammar_lookup(rules: List[Rule], expression: str, db:database.Database=None, tags: List[str] = ["*"], role: str = None, path: List = []):
    """
    Recursively looks up what form is the expression in
    Top level call: grammar_lookup(rules, expression)
    rules - list of grammar rules to use for lookup
    expression - a conjugated Japanese expression
    tags - list of glob patterns for possible tags of the expression
    role - grammatical role of the current expression (None=any role)
    path - holds the traversed path to the current expression
    """
    if len(path) > 10:
        #  raise RuntimeError()
        return None
    # find applicable rules
    applicable = set()
    for rule in rules:
        if role not in [None, rule.role]:
            continue # skip rules with unmatching role
        if not expression.endswith(rule.pattern):
            continue # skip rules with unmatching pattern
        # take rules that contain a matching tag
        for tag in tags:
            # tag is a glob pattern
            if rule.pos and fnmatch(rule.pos, tag):
                applicable.add((expression[:len(expression)-len(rule.pattern)]+rule.target_pattern, rule.pos, rule.traget))
                break
            elif not rule.pos:
                for pos in rule.pos_globs:
                    if fnmatch(pos, tag):
                        applicable.add((expression[:len(expression)-len(rule.pattern)] + rule.target_pattern, " ".join(rule.pos_globs[:]), rule.traget))
                        break
            else:
                pass # explicit, so that it is clear
    if len(applicable) == 0:
        print(path)
        return None
    for rule in applicable:
        if rule[2] == "plain":
            if not db:
                return path + [rule]
            if db.find_exact(rule[0]):
                return path + [rule]
        result = grammar_lookup(rules, rule[0], db, rule[1].split(), rule[2], path + [rule])
        if result:
            return result
    return None # can be shortened



if __name__ == "__main__":
    # for rule in parse_rules():
    #     print(repr(rule))
    rules = parse_rules()
    db = database.connect()
    result = grammar_lookup(rules, "書いてた", db)
    pass

"""
'(書いてた, *, None)': '(書いてつ, v5[^r]* v5r vs-c, plain) (書いてつ, v1, plain) (書いてる, v1*, plain)'
'(書いてつ, v5[^r]* v5r vs-c, plain)': X
'(書いてつ, v1, plain)': X
'(書いてる, v1*, plain)': '(書いている, v1, continuous)' => X /// should create (書いて, v[15]* vk vs-*, て-form)
continuous plain 〜いる v1 for て-form 〜 v[15]* vk vs-*
^^^^^^      ^------------ so what is this?!
this should be used

"""