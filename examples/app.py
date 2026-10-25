from fluxscript import App, Page, Heading, Text, Button, Input

app = App("Research Manager")
home = Page("/", title="Research Manager")
home.add(Heading("Welcome to Research Manager"))
home.add(Text("Write a declarative Python description; generate target-specific project starters."))
home.add(Input("Project name", name="project_name"))
home.add(Button("Save project", action="save_project"))
app.add_page(home)
