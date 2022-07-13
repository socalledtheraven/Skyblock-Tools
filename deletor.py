import os

def delete(path):
  directory = os.fsencode(path)
  for file in os.listdir(directory):
    filename = os.fsdecode(file)
    print(filename)
    if filename != ".replit" and filename[0] == ".":
      os.remove(f"{path}/{filename}")