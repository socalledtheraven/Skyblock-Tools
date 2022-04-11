from flask import Flask, render_template
import main

app = Flask(__name__, template_folder="templates")

#Repo.clone_from("https://github.com/Moulberry/NotEnoughUpdates-REPO.git", "./neu-repo/")

@app.route("/")
def index():
  return render_template("index.html")

@app.route("/bazaarflipper", methods=["GET", "POST"])
def bz_flipper():
  main.build_table(main.bazaar_flipper(), "./templates/bazaar_flipper_data.html")
  return render_template("bazaarflipper.html")

@app.route("/craftflipper", methods=["GET", "POST"])
def craft_flipper():
  main.build_table(main.craft_flipper(), "./templates/craft_flipper_data.html")
  return render_template("craftflipper.html")

if __name__ == "__main__":
  app.run(host='0.0.0.0', debug=True, port=8080)