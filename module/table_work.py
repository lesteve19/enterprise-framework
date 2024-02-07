import boto3
import botocore
import json
import sys
from string import Template
# from jira import JIRA
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
    {"Change Control": ["System Owner Gate", "Security Owner Gate", "Technical Gate"]},
    {"Documentation": ["ReadMe", "Central KB"]},
    {"Monitoring": ["Config"]},
    {"Reporting": ["Pipeline Reports", "Scheduled Reports"]},
    {"Security": ["IAM", "Network", "Data Mgmt", "Secrets Mgmt"]}
]



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
        sector = row["sector"]["S"]
        solution = row["solution"]["S"]
        comp["compname"]=compname
        comp["action"]=action
        comp["category"]=category
        comp["currentpoints"]=currentpoints
        comp["integration"]=integration
        comp["maxpoints"]=maxpoints
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
        proj["projname"]=projname
        proj["jiraid"]=jiraid
        proj_map.append(proj)

    return proj_map


#-----Grab token and create jira connection-----#
# def jira_conn():
#     try:
#         get_secret_value_response = sec_client.get_secret_value(
#             SecretId=secret_name
#         )
#     except ClientError as e:
#         raise e

#     api_token = get_secret_value_response['SecretString']
#     api_token = json.loads(api_token)
#     jira = JIRA(server=jira_server, basic_auth=(jira_user, api_token["api_token"]))

#     return jira



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
#----------SOURCE OF TRUTH READ IN----------#
#-------------------------------------------#

#---Gathers existing competency and project info (if any) from the DynamoDB tables---#
table_c_list = get_comps(db_client)
table_p_list = get_projs(db_client)

#---Reads the master csv file---#
core_list = open("core.csv").read().splitlines()

#---Lists for comparing the master list against the dynamo tables---#
core_comps = [] # Just the competency names from the master list #
core_projs = [] # Just the project names from the master list #
table_comps = [] # Just the competency names from table scan #
table_projs = [] # Just the project names from the table scan #
# jira = jira_conn()

#---Adds just the names of competencies and projects gathered from the DynamoDB tables---#
for c in table_c_list:
    table_comps.append(c["compname"])
for p in table_p_list:
    table_projs.append(p["projname"])

#---Iterate through each line in master list and take actions based on status---#
print("--------------------COMPETENCIES--------------------")
for entry in core_list:
    #-Grab competency name from master list-#
    comp_itself = entry.split(',', 1)[0]
    core_comps.append(comp_itself)
    #-Grab associated project names from master list-#
    comp_projects = entry.split(',', 1)[1]
    comp_projects = comp_projects.replace('"','')
    comp_projects = comp_projects.split(',')
    for cproject in comp_projects:
        core_projs.append(cproject)

    #---Check to see if competency from master list exists in dynamo table---#
    if comp_itself not in table_comps:
        components = comp_itself.split('-')
        c_data = dict(
            sector = components[0],
            category = components[1],
            action = components[2],
            solution = components[3],
            integration = components[4],
            current_points = 0,
            max_points = len(comp_projects)*10,
            project_list = comp_projects,
        )

        #---Populate competency table---#
        print(f'POPULATING {comp_itself}')
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


#---Check to see if project from master list exists in dynamo table---#
core_projs = list(set(core_projs))
print("--------------------PROJECTS--------------------")
for proj in core_projs:
    if proj not in table_projs:
        
        # Do JIRA creation here

        p_data = dict(
            project_name = proj,
        )
            # jira_id = ,
        #---Populate projects table---#
        print(f'POPULATING {proj}')
        with open('proj_table_template.json', 'r') as p_json_file:
            p_content = ''.join(p_json_file.readlines())
            p_template = Template(p_content)
            p_configuration = json.loads(p_template.substitute(p_data))
            db_client.put_item(
                TableName = proj_table,
                Item = p_configuration
            )
    
    else:
        print(f'.....{proj} .....already exists')
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






#----------------------------------------#
#----------TABLE CONFIGURATIONS----------#
#----------------------------------------#













# issue_dict = {
#     'project': {'id': jira_proj_id},
#     'summary': f'{proj_title}',
#     'description': 'This project is needed to achieve/improve the {} competency(ies)',
#     'issuetype': {'name': 'Epic'},
#     'labels': [f'entfrm-{sector}'],
# }


# issues = jira.search_issues(f'project = {jira_proj_id} ORDER BY created ASC')
# for issue in issues:
#     issue_type = issue.fields.issuetype
#     issue_status = issue.fields.status
#     print(f'{issue} is a/an {issue_type} and in the following status: {issue_status}')
    
    
    
    # if str(issue_type) == "Story":
    #     print("HOOOOORAYYY")
    #     issue.update(fields=issue_dict)





# jira.create_issue(fields=issue_dict)


# projects = jira.projects()
# print(projects)

# for project in projects:
#     print(project)






















    
    

# #-----Read Projects table and format list-----#
# def get_projs(client):
#     proj_map = []
#     proj_contents = client.scan(TableName=proj_table)
#     for row in comp_contents['Items']:
#         print("DO STUFF")






# #-----Calculate points-----#
# current_points = []
# total_points = []
# table_c_list = get_comps(db_client)
# sector_list = []
# s_list = []

# for comp in table_c_list:
#     if comp["sector"] not in sector_list:
#         sector_list.append(comp["sector"])
#         sector_dict = {"sector": comp["sector"], "current": comp["currentpoints"], "max": comp["maxpoints"], "total": 1}
#         s_list.append(sector_dict)
#     else:
#         for s in s_list:
#             if s["sector"] == comp["sector"]:
#                 newcurrent = int(s["current"])+int(comp["currentpoints"])
#                 newmax = int(s["max"])+int(comp["maxpoints"])
#                 newtotal = s["total"]+1
#                 s.update({"sector": comp["sector"], "current": int(newcurrent), "max": int(newmax), "total": int(newtotal)})
#     current_points.append(int(comp["currentpoints"]))
#     total_points.append(int(comp["maxpoints"]))


# for sec in s_list:
#     per = int(sec["current"])/int(sec["max"])
#     print("-----------------------------------------------")
#     print("-----------------------------------------------")
#     print(f'{sec["sector"].upper()} SECTOR')
#     print(f'{sec["sector"]} has {sec["total"]} core competencies')
#     print(f'Current {sec["sector"]} points:  {sec["current"]}')
#     print(f'Total {sec["sector"]} points:    {sec["max"]}')
#     print(f'{sec["sector"]} percentage:  {round(per*100,2)}%')

# cp = sum(current_points)
# tp = sum(total_points)
# pp = cp/tp
# percent = round(pp*100,2)

# print("-----------------------------------------------")
# print("-----------------------------------------------")
# print("-----------------------------------------------")
# print("-----------------------------------------------")
# print("TOTALS")
# print(f'Total core competencies:  {len(table_c_list)}')
# print(f'Current points achieved:  {cp}')
# print(f'Total possible points:    {tp}')
# print(f'Total percentage:         {percent}%')
# print("-----------------------------------------------")
# print("-----------------------------------------------")