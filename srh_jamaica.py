import os
import json
import subprocess
import tempfile
import shutil

from rpft.converters import create_flows
from rapidpro_abtesting.main import apply_abtests

def srh_jamaica_pipeline():

    srh_registration_ID = "1yett-Rfzb9Ou8IQ1kwtrKPN_auhM-lk66r9gkqNV1As"
    srh_entry_ID = "19xvYfwWKA1hT5filGPWYEobQL1ZFfcFbTj1-aJCN8OQ"
    srh_content_ID = "1Tcg02_EW3GltlbL8ee-1QkGB8qVY1m0lFRgd-qIMqMM"
    srh_safeguarding_ID = "1A_p3cb3KNgX8XxD9MlCIoa294Y4Pb9obUKfwIvERALY"

    outputpath = "./output/"

    default_expiration = 180
    special_expiration = "./edits/expiration_times.json"

    ab_testing_sheet_id = '1SDUUCbDL1-oW7b9pB2RqfM6HqB-jeLDAdT3Ng6e515I'
    
    select_phrases = ".\edits\select_phrases.json"
    special_words = ".\edits\special_words.json"
    count_threshold = "2"
    length_threshold = "18"
    qr_limit = "10"

    sg_path = "./edits/safeguarding_srh.json"
    sg_flow_name = "SRH - Safeguarding - WFR interaction"
    sg_flow_id = "ecbd9a63-0139-4939-8b76-343543eccd94"

    redirect_flow_names = (
    '['
    '    "SRH - Safeguarding - Redirect to topic"'
    ']'
)
    

    sources = [
        # {
        #     "filename": "srh_registration",
        #     "spreadsheet_ids": [
        #         srh_registration_ID         
        #     ],
        #     "tags": [],
        #     "outputlog": False
        # },
        {
            "filename": "srh_entry",
            "spreadsheet_ids": [
                srh_entry_ID,
                srh_safeguarding_ID         
            ],
            "tags": [],
            "outputlog": False
        },
        {
            "filename": "srh_content_menstruation_pregnancy_puberty",
            "spreadsheet_ids": [
                srh_content_ID         
            ],
            "tags": [3, "menstruation_pregnancy_puberty"],
            "outputlog": False
        },
        {
            "filename": "srh_content_stis",
            "spreadsheet_ids": [
                srh_content_ID         
            ],
            "tags": [3, "stis"],
            "outputlog": False
        },
        {
            "filename": "srh_content_contraceptives",
            "spreadsheet_ids": [
                srh_content_ID         
            ],
            "tags": [3, "contraceptives"],
            "outputlog": False
        },
        {
            "filename": "srh_content_gender_abstinence_mental_violence_relation",
            "spreadsheet_ids": [
                srh_content_ID         
            ],
            "tags": [3, "gender_abstinence_mental_violence_relation"],
            "outputlog": False
        }
    ]

    for source in sources:

        source_file_name = source["filename"]
        spreadsheet_ids = source["spreadsheet_ids"]
        tags = source["tags"]

        print("Processing: "+source_file_name)

        if not os.path.exists(outputpath):
            os.makedirs(outputpath)

        with tempfile.TemporaryDirectory() as temp_dir:

            if source["outputlog"]:
                logpath = "./log"
                if not os.path.exists(logpath):
                    os.makedirs(logpath)
            else:
                logpath = temp_dir

            #####################################################################
            # Step 1: Load google sheets and convert to RapidPro JSON
            #####################################################################

            output_path_1_1 = os.path.join(logpath, source_file_name + "_1_load_from_sheets.json")
            flows = create_flows(
                spreadsheet_ids,
                None,
                "google_sheets",
                data_models="models.srh_models",
                tags=tags,
            )

            with open(output_path_1_1, "w") as export:
                json.dump(flows, export, indent=4)

            input_path_2 = update_expiration_time(source, default_expiration, special_expiration, output_path_1_1, logpath)

            print("  Step 1 complete, google sheets converted to JSON")

            #####################################################################
            # Step 2: Flow edits 
            #####################################################################

            ab_log_file_path = os.path.join(logpath, "2_ab_testing.log")

            if ab_testing_sheet_id:
            
                output_path_2 = os.path.join(logpath, source_file_name + "_2_flow_edits.json")

                input_sheets = [ab_testing_sheet_id]

                apply_abtests(
                    input_path_2,
                    output_path_2,
                    input_sheets,
                    "google_sheets",
                    ab_log_file_path,
                )
                
                print("  Step 2 complete, added A/B tests and localization")
            else:
                output_path_2 = input_path_2
                print("  Step 2 skipped, no AB testing sheet ID provided")

            #####################################################################
            # step 3: modify quick replies
            #####################################################################

            output_file_name_3 = source_file_name + "_3_QR_modified"
            
            run_node(
                "idems_translation_chatbot/index.js",
                "reformat_quick_replies",
                output_path_2,
                select_phrases,
                output_file_name_3,
                logpath,
                count_threshold,
                length_threshold,
                qr_limit,
                special_words,
            )

            print("  Step 3 complete, reformatted quick replies")

            #####################################################################
            # step 4: implement safeguarding
            #####################################################################

            input_path_4 = os.path.join(logpath, output_file_name_3 + ".json")
            output_path_4 = os.path.join(logpath, source_file_name+"_4_safeguarding.json")

            if (
                sg_path
                and sg_flow_name
                and sg_flow_id
            ):

                run_node(
                    "safeguarding-rapidpro/srh_add_safeguarding_to_flows.js",
                    input_path_4,
                    sg_path,
                    output_path_4,
                    sg_flow_id,
                    sg_flow_name
                    )

                run_node(
                    "safeguarding-rapidpro/v2_edit_redirect_flow.js",
                    output_path_4,
                    sg_path,
                    output_path_4,
                    redirect_flow_names
                )

                print(
                    "  Step 4 complete, adding safeguarding flows and edited redirect flows"
                )
            else:
                output_path_4 = input_path_4
                print("  Step 4 skipped, no safeguarding details provided")

            #####################################################################
            # step 5: copy finished file to final localtion
            #####################################################################

            copy_file(output_path_4, outputpath, source_file_name+".json")

            print("  " + source_file_name + " successfully processed, result stored in output folder") 
        

def update_expiration_time(source, default_expiration, special_expiration, in_fp, outputpath):
    with open(special_expiration, "r") as specifics_json:
        specifics = json.load(specifics_json)

    with open(in_fp, "r") as in_json:
        org = json.load(in_json)

    for flow in org.get("flows", []):
        set_expiration(flow, default_expiration, specifics)

    out_fp = os.path.join(
        outputpath,
        source["filename"] + "_1_2_modified_expiration_times.json",
    )
    with open(out_fp, "w") as out_json:
        json.dump(org, out_json)

    return out_fp

def set_expiration(flow, default, specifics={}):
    expiration = specifics.get(flow["name"], default)

    flow["expire_after_minutes"] = expiration

    if "expires" in flow.get("metadata", {}):
        flow["metadata"]["expires"] = expiration

    return flow

def run_node(script, *args):
    subprocess.run(["node", "node_modules/@idems/" + script, *args])

def copy_file(src_path, dest_dir, new_name=None):
    try:
        # Ensure the source file exists
        if not os.path.exists(src_path):
            raise FileNotFoundError(f"The source file '{src_path}' does not exist.")

        # Create the destination directory if it doesn't exist
        os.makedirs(dest_dir, exist_ok=True)

        # Determine the new name of the file
        if new_name is None:
            new_name = os.path.basename(src_path)

        # Construct the full destination path
        dest_path = os.path.join(dest_dir, new_name)

        # Copy the file
        shutil.copy2(src_path, dest_path)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    
    srh_jamaica_pipeline()

