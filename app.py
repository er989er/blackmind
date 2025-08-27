import streamlit as st
import networkx as nx
from pyvis.network import Network
import tempfile, os, json, hashlib, uuid

st.set_page_config(page_title="Black Mind", layout="wide")

# -------------------------------
# Helper functions
# -------------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_json(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    else:
        return {}

def save_json(data, file):
    with open(file, "w") as f:
        json.dump(data, f)

# -------------------------------
# Load users and tokens
# -------------------------------
USERS_FILE = "users.json"
TOKENS_FILE = "tokens.json"

users = load_json(USERS_FILE)
tokens = load_json(TOKENS_FILE)

# -------------------------------
# Session state
# -------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "login_token" not in st.session_state:
    st.session_state.login_token = ""

# Check token for remember me
if not st.session_state.logged_in and st.session_state.login_token in tokens:
    st.session_state.logged_in = True
    st.session_state.username = tokens[st.session_state.login_token]

# -------------------------------
# Logout function
# -------------------------------
def logout():
    token = st.session_state.get("login_token")
    if token in tokens:
        del tokens[token]
        save_json(tokens, TOKENS_FILE)
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.login_token = ""
    st.experimental_rerun()

# -------------------------------
# Login / Register
# -------------------------------
if not st.session_state.logged_in:
    st.title("Black Mind Login")

    option = st.radio("Select:", ["Login", "Register"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    remember = st.checkbox("Remember Me")

    if st.button(option):
        if option == "Register":
            if username in users:
                st.error("Username already exists")
            else:
                users[username] = hash_password(password)
                save_json(users, USERS_FILE)
                st.success("User registered! You can now log in.")
        else:  # Login
            if username in users and users[username] == hash_password(password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Welcome back, {username}!")

                # Remember Me token
                if remember:
                    token = str(uuid.uuid4())
                    st.session_state.login_token = token
                    tokens[token] = username
                    save_json(tokens, TOKENS_FILE)
            else:
                st.error("Invalid username or password")

# -------------------------------
# Main App
# -------------------------------
else:
    st.title("Black Mind")
    st.subheader(f"Simple Mind Map Viewer (Dark Mode) - Logged in as {st.session_state.username}")

    if st.button("Logout"):
        logout()

    st.write("Type connections in the form `Parent -> Child -> Grandchild`, one per line.")

    example_text = """Math -> Algebra
Math -> Calculus
Science -> Physics
Science -> Chemistry
History -> Ancient
History -> Modern"""

    notes = st.text_area("Connections:", example_text, height=200)

    if st.button("Generate Mind Map"):
        G = nx.DiGraph()
        lines = [line.strip() for line in notes.split("\n") if "->" in line]

        # Handle multi-level connections
        for line in lines:
            parts = [x.strip() for x in line.split("->")]
            for i in range(len(parts) - 1):
                parent = parts[i]
                child = parts[i + 1]
                G.add_node(parent)
                G.add_node(child)
                G.add_edge(parent, child)

        net = Network(
            height="700px",
            width="100%",
            bgcolor="#121212",
            font_color="white",
            directed=True
        )
        net.from_nx(G)

        # Node styling
        for node in net.nodes:
            node["color"] = "#1f77b4"
            node["borderWidth"] = 2
            node["font"] = {"color": "white"}

        # Edge styling
        for edge in net.edges:
            edge["color"] = "gray"

        net.repulsion(node_distance=160, spring_length=160)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
            net.save_graph(tmp_file.name)
            tmp_path = tmp_file.name

        with open(tmp_path, "r", encoding="utf-8") as f:
            html_code = f.read()
            st.components.v1.html(html_code, height=750, scrolling=True)

        os.remove(tmp_path)
