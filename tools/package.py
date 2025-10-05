import os
import shutil

def delete_pycache_dirs(directory: str):
    for root, dirs, files in os.walk(directory):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                dir_path = os.path.join(root, dir_name)
                shutil.rmtree(dir_path)
                full_path = os.path.abspath(dir_path)
                print(f"Deleted: {full_path}")

def zip_directory(directory: str, name: str):
    base_name = os.path.join(os.path.dirname(os.getcwd()), name)
    shutil.make_archive(base_name, 'zip', directory)
    full_path = os.path.abspath(f"{base_name}.zip")
    print(f"Directory zipped as: {full_path}")

if __name__ == '__main__':
    dir_name = os.path.abspath(os.path.join(__file__, os.pardir))
    os.chdir(dir_name)

    directory = "../NodeToPython"
    zip_name = "NodeToPython"

    delete_pycache_dirs(directory)
    zip_directory(directory, zip_name)
