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
        path, entry = grammar.lookup(rules, "書いてた", db, verbous=True)
        for i in range(len(path) - 1):
            print("{}{} is {} for {}".format(" "*i, path[i][0], path[i+1][2], path[i+1][0]))
        print("Dictionary entry for: {} {}".format(path[-1][0], path[-1][1]))
        print(" ".join(entry["writings"]))
        print(" ".join(entry["readings"]))
        print(", ".join(entry["senses"][0]["glosses"]))
        

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
