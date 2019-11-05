from flask import Flask, render_template, send_from_directory

app = Flask("Packit Service Dashboard")


@app.route("/")
def main():
    return render_template('main_frame.html', header="Main Page", content="Info about packit service with links")


@app.route("/status/")
def status():
    return render_template('main_frame.html', header="Status of packit service", content="no status")


@app.route("/logs/")
def logs():
    return render_template('main_frame.html', header="Logs", content="nic")


@app.route('/node_modules/<path:filename>')
def node_modules(filename):
    return send_from_directory(f"node_modules", filename)


if __name__ == "__main__":
    app.run(debug=True)
