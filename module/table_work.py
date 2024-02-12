import boto3
import botocore
import json
import sys
from string import Template
from jira import JIRA
from botocore.exceptions import ClientError



#------------------------------------#
#----------GLOBAL VARIABLES----------#
#------------------------------------#

region = "us-east-2"
project = sys.argv[1]
comp_table = f'{project}-competencies'
proj_table = f'{project}-projects'
secret_name = "jira_token"
db_client = boto3.client('dynamodb', region_name=region)
sec_client = boto3.client('secretsmanager', region_name=region)
jira_server = "https://keepitsts.atlassian.net"
jira_user = "steven.lecompte@simpletechnology.io"
jira_proj_id = 10069

checklist = [
    {"Alerting": ["Thresholds", "Notifications"]},
    {"Automation": ["Code/Version Control", "IAC", "Config Mgmt", "Functional Tests", "Security Tests"]},
    {"Redundancy": ["High Availability", "Disaster Recovery"]},
    {"Change_Control": ["System Owner Gate", "Security Owner Gate", "Technical Gate"]},
    {"Documentation": ["ReadMe", "Central KB"]},
    {"Monitoring": ["Config"]},
    {"Reporting": ["Pipeline Reports", "Scheduled Reports"]},
    {"Security": ["IAM", "Network", "Data Mgmt", "Secrets Mgmt"]}
]

tasks = 0
for task in checklist:
    key = list(task.keys())[0]
    for value in task[key]:
        tasks = tasks +1

#-----------------------------#
#----------FUNCTIONS----------#
#-----------------------------#

#-----Read Competencies table and format list-----#
def get_comps(client):
    comp_map = []
    comp_contents = client.scan(TableName=comp_table)
    for row in comp_contents['Items']:
        comp = {}
        compname = row["competency"]["S"]
        action = row["action"]["S"]
        category = row["category"]["S"]
        currentpoints = row["current-points"]["N"]
        integration = row["integration"]["S"]
        maxpoints = row["max-points"]["N"]
        projectlist = row["project-list"]["S"]
        sector = row["sector"]["S"]
        solution = row["solution"]["S"]
        comp["compname"]=compname
        comp["action"]=action
        comp["category"]=category
        comp["currentpoints"]=currentpoints
        comp["integration"]=integration
        comp["maxpoints"]=maxpoints
        comp["projectlist"]=projectlist
        comp["sector"]=sector
        comp["solution"]=solution
        comp_map.append(comp)

    return comp_map


#-----Read Projects table and format list-----#
def get_projs(client):
    proj_map = []
    proj_contents = client.scan(TableName=proj_table)
    for row in proj_contents['Items']:
        proj = {}
        projname = row["project"]["S"]
        jiraid = row["jira-id"]["S"]
        proj["projname"]=projname.strip()
        proj["jiraid"]=jiraid
        proj_map.append(proj)

    return proj_map


#-----Grab token and create jira connection-----#
def jira_conn():
    try:
        get_secret_value_response = sec_client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    api_token = get_secret_value_response['SecretString']
    api_token = json.loads(api_token)
    jira = JIRA(server=jira_server, basic_auth=(jira_user, api_token["api_token"]))

    return jira



#----------------------------#
#----------WORKFLOW----------#
#----------------------------#

#-----Read in master list
#-----For each line in the master list:
    #---Check to see if competency already exists in competency table
        #--If competency doesn't exist in table:
            #-Populate competency table
            #-If projects required exist in project table and are in JIRA, continue
            #-Else populate project table and JIRA Epics (projects)
        #--If competency exists:
            #-If projects required exist in both project table and JIRA Epics (projects), continue
            #-Else: 
                #Create JIRA Epics for projects and grab number IDS (incase title gets changed)
                #Create JIRA Stories under the Epics based on 8 categories in checklist
                #Populate projects table

#-----Grab JIRA Epic (project) info:
    #---Rescan competency table for updated scores
    #---Status and number of stories/tasks
    #---Update table current and max points for competency
    #---Calculate totals



#-------------------------------------------#
#----------FOUNDATION FILE READ IN----------#
#-------------------------------------------#

#---Reads the origination csv file---#
core_list = open("foundations.csv").read().splitlines()



#---------------------------------------------------------#
#----------INITIAL TABLE AND JIRA CONFIGURATIONS----------#
#---------------------------------------------------------#

#---Lists for comparing the master list against the dynamo tables---#
core_comps = [] # Just the competency names from the foundation list #
proj_map = [] # Just the project names from the foundation list #
table_comps = [] # Just the competency names from table scan #
table_projs = [] # Just the project names from the table scan #

#---Gathers existing competency and project info (if any) from the DynamoDB tables---#
table_c_list = get_comps(db_client)
table_p_list = get_projs(db_client)

#---Adds just the names of competencies and projects gathered from the DynamoDB tables---#
for c in table_c_list:
    table_comps.append(c["compname"])
for p in table_p_list:
    table_projs.append(p["projname"])


print("----------------------------------------------------")
print("--------------------COMPETENCIES--------------------")
print("----------------------------------------------------")
#---Iterate through each line in master list and create separate objects---#
for entry in core_list:
    #-Grab competency name from master list-#
    comp_itself = entry.split(',', 1)[0]
    components = comp_itself.split('-')
    core_comps.append(comp_itself)
    #-Grab associated project names from master list-#
    comp_projects = entry.split(',', 1)[1]
    comp_projects = comp_projects.replace('"','')
    comp_projects = comp_projects.split(',')
    for cproject in comp_projects:
        proj_dict = {}
        proj_dict["projname"]=cproject
        proj_dict["projsector"]=components[0]
        proj_map.append(proj_dict)

    #---Check to see if competency from master list exists in dynamo table---#
    if comp_itself not in table_comps:
        c_data = dict(
            sector = components[0],
            category = components[1],
            action = components[2],
            solution = components[3],
            integration = components[4],
            current_points = 0,
            max_points = len(comp_projects)*tasks,
            project_list = comp_projects,
        )

        #---Populate competency table---#
        print(f'POPULATING {comp_itself} in Competency DynamoDB table...')
        with open('comp_table_template.json', 'r') as c_json_file:
            c_content = ''.join(c_json_file.readlines())
            c_template = Template(c_content)
            c_configuration = json.loads(c_template.substitute(c_data))
            db_client.put_item(
                TableName = comp_table,
                Item = c_configuration
            )

    else:
        print(f'.....{comp_itself} .....already exists')
        continue

#-----Delete any competencies that are no longer used-----#
for c in table_c_list:
    if c["compname"] not in core_comps:
        print(f'REMOVING {c["compname"]} from table, as it is no longer in the primary competency list')
        db_client.delete_item(
            TableName = comp_table,
            Key = {
                "competency": {
                    "S": c["compname"]
                }
            }
            )


print("------------------------------------------------")
print("--------------------PROJECTS--------------------")
print("------------------------------------------------")
#---Check to see if project from master list exists in dynamo table---#
core_projs = [i for n, i in enumerate(proj_map) if i not in proj_map[:n]]
jira = jira_conn()
for proj in core_projs:
    projname = proj["projname"].strip()
    if projname not in table_projs:
        epic_dict = {
            'project': {'id': jira_proj_id},
            'summary': f'{projname}',
            'description': f'{projname}',
            'issuetype': {'name': 'Epic'},
            'labels': [f'entfrm-sect-{proj["projsector"]}'],
        }
        ejid = jira.create_issue(fields=epic_dict)
        print("-----------")
        print(f'{ejid} has been created as an Epic issue for {projname}...')
        print("------")

        for task in checklist:
            key = list(task.keys())[0]
            for value in task[key]:
                story_dict = {
                    'project': {'id': jira_proj_id},
                    'summary': f'{key}-{value}-{projname}',
                    'description': f'{key}-{value}-{projname}',
                    'issuetype': {'name': 'Story'},
                    'labels': [f'entfrm-sect-{proj["projsector"]}', f'entfrm-imp-{key}'],
                    'parent': {'key': f'{ejid}'},
                }
            
                sjid = jira.create_issue(fields=story_dict)
                print(f'{sjid} has been created as a story under the Epic {ejid} for {key}-{value}-{projname}...')

        p_data = dict(
            project_name = projname,
            jira_id = ejid,
        )

        #---Populate projects table---#
        print("----------------")
        print(f'POPULATING {projname} in Projects DynamoDB table...')
        with open('proj_table_template.json', 'r') as p_json_file:
            p_content = ''.join(p_json_file.readlines())
            p_template = Template(p_content)
            p_configuration = json.loads(p_template.substitute(p_data))
            db_client.put_item(
                TableName = proj_table,
                Item = p_configuration
            )
    
    else:
        print(f'.....{projname} .....already exists')
        continue


#---DELETE PROJECTS SECTION HERE---#



#############  LEFT OFF HEERE  CHECK JIRA STORY STATUS LINKED TO AN EPIC AND THEN UPDATE TABLE POINTS

table_c_list = get_comps(db_client)
# table_p_list = get_projs(db_client)
jira = jira_conn()

issues = jira.search_issues(f'project = {jira_proj_id} AND parent = "ENTFRM-1139"')
for issue in issues:
    issue.delete()

issues = jira.search_issues(f'project = {jira_proj_id} AND parent = "ENTFRM-1161"')
for issue in issues:
    issue.delete()

# p_status = []

# for p in table_p_list:
#     p_dict = {}
#     child_issues = 0
#     done_issues = 0
#     jira_id = p["jiraid"]
#     p_dict["jiraid"]=jira_id
#     issues = jira.search_issues(f'project = {jira_proj_id} AND parent = {jira_id}')
#     for issue in issues:
#         child_issues = child_issues + 1
#         # issue_type = issue.fields.issuetype
#         issue_status = issue.fields.status
#         if str(issue_status) == "Done":
#             done_issues = done_issues + 1
#     p_dict["done"]=done_issues
#     p_status.append(p_dict)
#     perc = int(done_issues)/int(child_issues)
#     # print(f'{p["projname"]} has {done_issues} of {child_issues} or {round(perc*100,2)} ')
print("--------------------------------BREAK--------------------------------")
for c in table_c_list:
    competency = c["compname"]
    print("--------------------------------------------------")
    print(competency)
    current_points = c["currentpoints"]
    projects = c["projectlist"].replace('[','').replace(']','').replace("'", "")
    projects = projects.split(",")
    print(projects)
    for project in projects:
        project = project.strip()
        print("--------------------------------------------------")
        print(project)
        response = db_client.get_item(
            TableName=proj_table,
            Key={
                'project': {'S': project}
            }
        )
        jid = response['Item']['jira-id']['S']
        print(jid)



        # print(f'{issue} is a/an {issue_type} and in the following status: {issue_status}')
#     # issue.delete()
    
    





#-----Calculate points-----#
current_points = []
total_points = []
table_c_list = get_comps(db_client)
sector_list = []
s_list = []

for comp in table_c_list:
    if comp["sector"] not in sector_list:
        sector_list.append(comp["sector"])
        sector_dict = {"sector": comp["sector"], "current": comp["currentpoints"], "max": comp["maxpoints"], "total": 1}
        s_list.append(sector_dict)
    else:
        for s in s_list:
            if s["sector"] == comp["sector"]:
                newcurrent = int(s["current"])+int(comp["currentpoints"])
                newmax = int(s["max"])+int(comp["maxpoints"])
                newtotal = s["total"]+1
                s.update({"sector": comp["sector"], "current": int(newcurrent), "max": int(newmax), "total": int(newtotal)})
    current_points.append(int(comp["currentpoints"]))
    total_points.append(int(comp["maxpoints"]))


for sec in s_list:
    per = int(sec["current"])/int(sec["max"])
    print("-----------------------------------------------")
    print("-----------------------------------------------")
    print(f'{sec["sector"].upper()} SECTOR')
    print(f'{sec["sector"]} has {sec["total"]} core competencies')
    print(f'Current {sec["sector"]} points:  {sec["current"]}')
    print(f'Total {sec["sector"]} points:    {sec["max"]}')
    print(f'{sec["sector"]} percentage:  {round(per*100,2)}%')

cp = sum(current_points)
tp = sum(total_points)
pp = cp/tp
percent = round(pp*100,2)

print("-----------------------------------------------")
print("-----------------------------------------------")
print("-----------------------------------------------")
print("-----------------------------------------------")
print("TOTALS")
print(f'Total core competencies:  {len(table_c_list)}')
print(f'Current points achieved:  {cp}')
print(f'Total possible points:    {tp}')
print(f'Total percentage:         {percent}%')
print("-----------------------------------------------")
print("-----------------------------------------------")