import os

def generate_code():
    folder_path = './app/'
    output_file = 'all_code.txt'

    input_files = []

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.py'):
                full_path = os.path.join(root, file)
                input_files.append(full_path)

    if os.path.exists(output_file):
        os.remove(output_file)

    with open(output_file, 'w') as outfile:
        for file_path in input_files:
            with open(file_path, 'r') as file:
                content = file.read()
                outfile.write(f"#{full_path}\n")
                outfile.write(content)
                outfile.write("\n\n")

generate_code()