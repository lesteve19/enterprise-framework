import boto3
import json
import sys
from string import Template

region = "us-east-1"
task_table = sys.argv[1]
db_client = boto3.client('dynamodb', region_name=region)

#-----Read table and format list-----#
def get_tasks(client):
    task_map = []
    table_contents = client.scan(TableName = task_table)
    for row in table_contents['Items']:
        task = {}
        taskname = row["target"]["S"]
        action = row["action"]["S"]
        category = row["category"]["S"]
        currentpoints = row["current-points"]["N"]
        integration = row["integration"]["S"]
        maxpoints = row["max-points"]["N"]
        sector = row["sector"]["S"]
        solution = row["solution"]["S"]
        task["taskname"]=taskname
        task["action"]=action
        task["category"]=category
        task["currentpoints"]=currentpoints
        task["integration"]=integration
        task["maxpoints"]=maxpoints
        task["sector"]=sector
        task["solution"]=solution
        task_map.append(task)

    return task_map


#-----Check that all tasks are populated in the table-----#
task_list = get_tasks(db_client)
core_list = open("task_list.txt").read().splitlines()
onlytasks = []
for t in task_list:
    onlytasks.append(t["taskname"])

for entry in core_list:
    if entry not in onlytasks:
        print(f'POPULATING {entry}')
        components = entry.split('-')
        data = dict(
            sector = components[0],
            category = components[1],
            action = components[2],
            solution = components[3],
            integration = components[4],
        )

        with open('table_template.json', 'r') as json_file:
            content = ''.join(json_file.readlines())
            template = Template(content)
            configuration = json.loads(template.substitute(data))
            db_client.put_item(
                TableName = task_table,
                Item = configuration
            )

    else:
        print(f'{entry} already exists')
        continue


#-----Calculate points-----#
current_points = []
total_points = []
task_list = get_tasks(db_client)
sector_list = []
s_list = []

for task in task_list:
    if task["sector"] not in sector_list:
        sector_list.append(task["sector"])
        sector_dict = {"sector": task["sector"], "current": task["currentpoints"], "max": task["maxpoints"], "total": 1}
        s_list.append(sector_dict)
    else:
        for s in s_list:
            if s["sector"] == task["sector"]:
                newcurrent = int(s["current"])+int(task["currentpoints"])
                newmax = int(s["max"])+int(task["maxpoints"])
                newtotal = s["total"]+1
                s.update({"sector": task["sector"], "current": int(newcurrent), "max": int(newmax), "total": int(newtotal)})
    current_points.append(int(task["currentpoints"]))
    total_points.append(int(task["maxpoints"]))


for sec in s_list:
    per = sec["current"]/sec["max"]
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
print(f'Total core competencies:  {len(task_list)}')
print(f'Current points achieved:  {cp}')
print(f'Total possible points:    {tp}')
print(f'Total percentage:         {percent}%')
print("-----------------------------------------------")
print("-----------------------------------------------")