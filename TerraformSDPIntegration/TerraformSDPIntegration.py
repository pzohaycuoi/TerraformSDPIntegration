from dotenv import load_dotenv
import os
import json
import TerraformApi
import SDP
import VCS


# load $COMPLETE_JSON_FILE from SDP
# input_file = sys.argv[1]
input_file = '../test/test-data.json'
try:
    opt_data = SDP.convert_json(input_file)
except AssertionError as err:
    raise SystemExit(err)

# load .env file and
# check if TOKEN and TF_ORG have value
config = load_dotenv()
TOKEN = os.getenv("TOKEN")
TF_ORG = os.getenv("TF_ORG")
REPO = os.getenv("REPO")
if (TOKEN == '') or (TOKEN is None):
    raise SystemExit("No dotenv with name TOKEN provided, exiting...")
if (TF_ORG == '') or (TF_ORG is None):
    raise SystemExit("No dotenv with name TF_ORG provided, exiting...")
if (REPO == '') or (REPO is None):
    raise SystemExit("No dotenv with name TF_ORG provided, exiting...")

# Get Terraform code from repository
repo_dir = VCS.git_clone(REPO, "../temp")
var_files = VCS.find_all("variables.tf", "../temp")
# get variable list
var_list = []
for file in var_files:
    var_list.append(VCS.get_tf_var(file))

# get unique value from var_list[] by convert to set
var_list = set(var_list)
var_list = list(var_list)

# Get SDP custom field values, base on Terraform variable file
# var_list = ["workspace_name", "db_name", "db_username", "db_password"]
field_list = SDP.get_field(opt_data)
field_name_list = list(field_list.keys())
matching_field_name = [field for field in field_name_list if field in var_list]
matching_field = {{field: val} for field, val in field_list if field in matching_field_name}

# Check if workspace field has value
ws_name = matching_field["workspace_name"]
if (ws_name == '') or (ws_name is None):
    SystemExit("No Terraform workspace name provided, exiting...")

# Create Terraform workspace
ws_create = TerraformApi.creation(TOKEN, TF_ORG, workspace_name=ws_name, auto_apply=False)
ws_create.raise_for_status()
ws_create_content = json.loads(ws_create.content)

# Create Terraform configuration version
ws_conf_create = TerraformApi.config(TOKEN, workspace_id=ws_create_content["data"]["id"], auto_queue=False)
ws_conf_create.raise_for_status()
ws_conf_content = json.loads(ws_conf_create)

# Get upload url from configuration version and upload Terraform code into workspace
ws_conf_upload = TerraformApi.upload_code(TOKEN, "cac", ws_conf_content["data"]["attributes"]["upload-url"])

# # get upload url from the configuration version
# ws_conf_upload_url = ws_conf_content["data"]["attributes"]["upload-url"]
# # upload configuration content file
# tar_file = [('file', open('../repo.tar.gz', 'rb'))]
# ws_upload_file_payload = {}
# ws_upload_file_response = api_request(ws_conf_upload_url, TOKEN, "PUT", {}, tar_file)
# print(ws_upload_file_response.text)