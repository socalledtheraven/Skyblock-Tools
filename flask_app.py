from flask import Flask, render_template, redirect
import main

app = Flask(__name__, template_folder="templates", subdomain_matching=True)
app.config['SERVER_NAME'] = "skyblocktools.me"

@app.route("/")
def index():
  return render_template("index.html")

@app.route("/api")
def api():
  return redirect(f"https://api.{app.config['SERVER_NAME']}/docs")

@app.route("/bazaar_flipper", methods=["GET", "POST"])
def bazaar_flipper():
  main.build_table(main.bazaar_flipper(), "./templates/bazaar_flipper_data.html")
  return render_template("bazaarflipper.html")

@app.route("/craft_flipper", methods=["GET", "POST"])
def craft_flipper():
  main.build_table(main.craft_flipper(), "./templates/craft_flipper_data.html")
  return render_template("craftflipper.html")

@app.route("/forge_flipper", methods=["GET", "POST"])
def forge_flipper():
  main.build_table(main.forge_flipper(), "./templates/forge_flipper_data.html")
  return render_template("forgeflipper.html")

if __name__ == "__main__":
  app.run(host='0.0.0.0', debug=True, port=8080)