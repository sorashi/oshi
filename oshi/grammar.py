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

def apply_rule_backward(expression: str, rule: Rule):
    return expression[:len(expression)-len(rule.pattern)] + rule.target_pattern

def apply_rule_forward(expression: str, rule: Rule):
    return expression[:len(expression)-len(rule.target_pattern)] + rule.pattern

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

def lookup(rules: List[Rule], expression: str, db: database.Database = None,
                   tags: List[str] = ["*"], role: str = None, path: List[Rule] = [], verbous = False):
    """
    Recursively looks up what form the expression is in
    Top level call: lookup(rules, expression, database)
    rules - list of grammar rules to use for lookup
    expression - a conjugated Japanese expression
    db - a database.Database
    tags - list of glob patterns for possible tags of the expression
    role - for example "plain", "past", or None = any role
    path - holds the traversed path to the current expression
    verbous - whether should print() information about the search

    retruns a tuple (path, database entry) or None if nothing was found
    """
    if type(db) is not database.Database:
        raise ValueError("Database invalid")
    if len(path) <= 0:
        entry = db.find_exact(expression)
        if entry:
            return path, entry
    if verbous:
        print("{}::({}, {}, {})::::".format("  " * len(path), expression, " ".join(tags), role))
    if len(path) > 20:
        raise RuntimeError("Possible recursion loop (depth limit reached)")
    # find applicable rules
    applicable = set()
    for rule in rules:
        if rule in path:
            continue # skip rules that have already been used
        if role not in [None, rule.rule, rule.role]:
            continue # skip rules with unmatching role
        if not expression.endswith(rule.pattern):
            continue # skip rules with unmatching pattern
        # take rules that contain a matching tag
        # the rule has a definitive pos
        if rule.pos:
            found = False
            for tag_glob in tags:
                if fnmatch(rule.pos, tag_glob):
                    applicable.add(rule)
                    found = True
                    break
            if found:
                continue
        for pos_glob in rule.pos_globs:
            found = False
            for tag_glob in tags:
                if fnmatch(pos_glob, tag_glob):
                    applicable.add(rule)
                    found = True
                    break
            if found:
                break

    if len(applicable) == 0:
        # no applicable rules found
        if verbous:
            print("  "*len(path) + "dead end")
        return None
    for rule in applicable:
        # new expression is built by removing the suffix in the pattern and replacing it with
        # target_pattern, for example 書いてた -> 書いてる
        new_expression = expression[:len(expression)-len(rule.pattern)] + rule.target_pattern
        if verbous:
            print("  "*len(path) + str(rule))
        if rule.traget == "plain":
            entry = db.find_exact(new_expression)
            if entry:
                # this node is the result
                return path + [rule], entry
        result = lookup(rules, new_expression, db,
                                rule.pos_globs, rule.traget, path + [rule], verbous)
        # if a result was found we return all the way up from this branch
        if result:
            return result
        # else the next rule branch will be explored

    return None # none of the applicable rules are correct

if __name__ == "__main__":
    rules = parse_rules()
    db = database.connect()
    expression = "書いてた"
    path, entry = lookup(rules, expression, db, verbous=True)
    t=0
    for rule in path:
        print("{}{} is {} for {}".format("  "*t, expression, rule.rule, apply_rule_backward(expression, rule)))
        expression = apply_rule_backward(expression, rule)
        t+=1
    print("Dictionary entry for: {} {}".format(expression, path[-1].pos_globs))
    print(" ".join(entry["writings"]))
    print(" ".join(entry["readings"]))
    print(", ".join(entry["senses"][0]["glosses"]))
