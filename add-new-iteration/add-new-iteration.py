from azure.devops.v7_0.work import TeamContext, TeamSettingsIteration
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

# Azure DevOps organization URL and personal access token
organization_url = ""
personal_access_token = ""

# New iteration path details
project_name = "se66projects"
iteration_path = "Backlog\\Sprint2"

# List of team names to update
team_names = ["Test", "TestSub1"]

def add_iteration_path_to_teams():
    # Create a connection to the organization
    credentials = BasicAuthentication('', personal_access_token)
    connection = Connection(base_url=organization_url, creds=credentials)

    # Get the iteration based on iteration path
    wit_client = connection.clients.get_work_item_tracking_client()
    iteration_node = wit_client.get_classification_node(project_name, 'iterations', path=iteration_path)
    iteration = TeamSettingsIteration(id=iteration_node.identifier)

    # Add the existing iteration to each team
    work_client = connection.clients.get_work_client()
    for team_name in team_names:
        team = TeamContext(project=project_name, team=team_name)
        work_client.post_team_iteration(iteration, team)
        print(f"Added '{iteration_path}' to the iteration paths of team '{team_name}'.")

    print("Iteration path update completed successfully.")

if __name__ == "__main__":
    add_iteration_path_to_teams()
