from .user_seeder import run as user_seeder

def run_all_seeders():

    print("Running seeders...")

    user_seeder()

    print("All seeders executed successfully")

if __name__ == "__main__":
    run_all_seeders()