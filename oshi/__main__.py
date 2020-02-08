"""
oshi -- Japanese grammar tester
"""
import threading
import database
import grammar
import itertools

db = None
def load_database():
    global db
    db = database.connect()

database_loading = threading.Thread(target=load_database)
database_loading.start() # start loading database in another thread

def menu_search():
    print("Type e or q at any time to exit")
    while True:
        search = input("search: ").strip()
        if search.lower() in ["e", "q"]:
            return
        results = db.search(search)
        count = 0
        for result in results:
            print(database.entry_tostring(result))
            # pagination every ten entries
            if count > 0 and count % 10 == 0 and input("Next page? (y/n) ").strip().lower() != "y":
                break
            count += 1

def menu_grammar():
    rules = grammar.parse_rules()
    print("Type e or q at any time to exit")
    while True:
        expression = input("g>> ").strip()
        if expression.lower().strip() in ["e", "q"]:
            return
        print("Recognizing...")
        path, entry = grammar.lookup(rules, expression, db, verbous=False) or (None, None)
        if path is None:
            print("Lookup failed, grammar form couldn't be recognized")
            continue
        t = 0
        for rule in path:
            print("{}{} is {} for {}".format("  "*t, expression, rule.rule, grammar.apply_rule_backward(expression, rule)))
            expression = grammar.apply_rule_backward(expression, rule)
            t += 1
        if len(path) <= 0:
            print("Dictionary entry for " + expression)
        else:
            print("Dictionary entry for: {} {}".format(expression, " ".join(path[-1].pos_globs)))
        print(database.entry_tostring(entry))

def menu_help():
    print("help")

print("Welcome to oshi")
while True:
    print()
    print("menu:")
    print("s - search")
    print("g - grammar")
    print("h - help")
    print("e - exit")
    choice = input(">> ").strip()

    if database_loading.is_alive():
        print("Loading database...")
    database_loading.join() # block until database finishes loading

    if choice == "s":
        menu_search()
    elif choice == "g":
        menu_grammar()
    elif choice == "h":
        menu_help()
    elif choice == "e":
        exit(0)
    else:
        print("Unknown choice")
