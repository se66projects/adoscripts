from azure.devops.v7_0.work import TeamContext, TeamSettingsIteration
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from tabulate import tabulate

def create_connection(organization_url, personal_access_token):
    credentials = BasicAuthentication("", personal_access_token)
    connection = Connection(base_url=organization_url, creds=credentials)
    return connection

def query_work_items(connection, area_path, iteration_path, carryover):
    wit_client = connection.clients.get_work_item_tracking_client()
    
    query = (
        f"SELECT [System.Id], [System.WorkItemType], [System.Title], [System.State], "
        f"[System.AssignedTo], [Microsoft.VSTS.Scheduling.Effort], [System.AreaPath], [System.Tags] "
        f"FROM workitems WHERE [System.WorkItemType] IN ('Product Backlog Item', 'Bug') "
        f"AND [System.AreaPath] UNDER '{area_path}' AND [System.IterationPath] UNDER '{iteration_path}' "
        f"AND [System.Tags] {'CONTAINS' if carryover else 'NOT CONTAINS'} 'Carryover' "
        "ORDER BY [Microsoft.VSTS.Common.BacklogPriority]"
    )
    
    wiql = {"query": query}
    result = wit_client.query_by_wiql(wiql)
    work_item_ids = [wi.id for wi in result.work_items]
    work_items = wit_client.get_work_items(ids=work_item_ids) if work_item_ids else []
    count = len(work_items)

    return count, work_items

def get_work_items_table(work_items, table_headers):
    table_data = []
    for work_item in work_items:
        table_data.append([
            f"#{work_item.id}",
            work_item.fields.get("System.AssignedTo", {}).get("displayName", "N/A"),
            work_item.fields.get("Microsoft.VSTS.Scheduling.Effort", "N/A"),
            work_item.fields.get("System.AreaPath", "N/A"),
            work_item.fields.get("System.Tags", "N/A")
        ])
    table = tabulate(table_data, headers=table_headers, tablefmt="pipe")

    return table

def print_backlog_items(organization_url, area_paths, iteration_path, output_file, personal_access_token):
    connection = create_connection(organization_url, personal_access_token)
    table_headers = ['Backlog Item', 'Assigned To', 'Effort', 'Area Path', 'Tags']

    summary_table_data = []
    area_path_counts = {}

    for area_path in area_paths:
        area_name = area_path.split("\\")[-1]
        carryover_count, carryover_items = query_work_items(connection, area_path, iteration_path, carryover=True)
        new_count, new_items = query_work_items(connection, area_path, iteration_path, carryover=False)
        total_count = carryover_count + new_count
        area_path_counts[area_path] = (area_name, carryover_count, carryover_items, new_count, new_items)
        summary_table_data.append([area_name, carryover_count, new_count, total_count, area_path])

    summary_table_headers = ['Area', 'Carryover', 'New', 'Total', 'Area Path']
    summary_table = tabulate(summary_table_data, headers=summary_table_headers, tablefmt="pipe")

    with open(output_file, "wt") as file:
        file.write("[[_TOC_]]\n")
        file.write("# Summary\n")
        file.write(summary_table)
        file.write("\n")

        for area_path in area_paths:
            area_name, carryover_count, carryover_items, new_count, new_items = area_path_counts[area_path]

            file.write(f"# Planned backlog items for {area_name}\n")
            file.write(f"- The number of all planned items: {carryover_count + new_count}\n")
            file.write(f"- The number of carryover items: {carryover_count}\n")
            file.write(f"- The number of new items: {new_count}\n")

            if carryover_count > 0:
                table = get_work_items_table(carryover_items, table_headers)
                file.write("## Carryover items\n")
                file.write(table)
                file.write("\n")

            if new_count > 0:
                table = get_work_items_table(new_items, table_headers)
                file.write("## New items\n")
                file.write(table)
                file.write("\n")

            file.write("\n")

if __name__ == "__main__":
    personal_access_token = ""
    organization_url = ""
    area_paths = [
        "se66projects\\TestRoot",
        "se66projects\\TestRoot\\TestSub1",
        "se66projects\\TestRoot\\TestSub2"
    ]
    iteration_path = "se66projects\\Backlog\\Sprint2"
    output_file = "snapshot.md"
    print_backlog_items(organization_url, area_paths, iteration_path, output_file, personal_access_token)
