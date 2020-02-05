"""
oshi -- Japanese grammar tester
"""
import threading
import database
import grammar

db = None
def load_database():
    global db
    db = database.connect()

def menu_search():
    print("Type e or q anytime to exit")
    while True:
        search = input("search: ").strip()
        if search.lower() in ["e", "q"]:
            return
        results = db.search(search)
        for result in results:
            print("{} ({}):".format(", ".join(result["writings"]), ", ".join(result["readings"])))
            for sense in result["senses"]:
                print("- " + ", ".join(sense["glosses"]))

def menu_grammar():
    rules = grammar.parse_rules()
    while True:
        expression = input("g>> ").strip()
        path, entry = grammar.lookup(rules, expression, db, verbous=True) or (None, None)
        if path is None:
            print("Lookup failed, grammar form couldn't be recognized")
            continue
        t = 0
        for rule in path:
            print("{}{} is {} for {}".format("\t"*t, expression, rule.rule, grammar.apply_rule_backward(expression, rule)))
            expression = grammar.apply_rule_backward(expression, rule)
            t += 1
        if len(path) <= 0:
            print("Dictionary entry for " + expression)
        else:
            print("Dictionary entry for: {} {}".format(expression, " ".join(path[-1].pos_globs)))
        print("\t" + " ".join(entry["writings"]))
        print("\t" + " ".join(entry["readings"]))
        print("\t" + ", ".join(entry["senses"][0]["glosses"]))

def menu_help():
    print("help")

database_loading = threading.Thread(target=load_database)
database_loading.start() # start loading database in another thread
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
