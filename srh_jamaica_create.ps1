
$srh_registration = "1yett-Rfzb9Ou8IQ1kwtrKPN_auhM-lk66r9gkqNV1As"
$srh_entry = "19xvYfwWKA1hT5filGPWYEobQL1ZFfcFbTj1-aJCN8OQ"
$srh_content = "1Tcg02_EW3GltlbL8ee-1QkGB8qVY1m0lFRgd-qIMqMM"
$srh_safeguarding ="1A_p3cb3KNgX8XxD9MlCIoa294Y4Pb9obUKfwIvERALY"

Set-Location "..\rapidpro-flow-toolkit"

<#
tags.2
menstruation
pregnancy
stis
puberty
contraceptives
gender_sexuality
abstinence
mental_health
violence
relationships
#>

<#
tags.3
menstruation_pregnancy_puberty
stis
contraceptives
gender_abstinence_mental_violence_relation
#>

##### create flows

#python main.py create_flows $srh_registration  -o ("..\srh-jamaica-chatbot\flows\srh_registration.json") --format=google_sheets --datamodels=tests.input.srh_chatbot.srh_models
#python main.py create_flows  $srh_entry $srh_safeguarding -o ("..\srh-jamaica-chatbot\flows\srh_entry.json") --format=google_sheets --datamodels=tests.input.srh_chatbot.srh_models
#python main.py create_flows  $srh_content -o ("..\srh-jamaica-chatbot\flows\srh_content_menstruation_pregnancy_puberty.json") --format=google_sheets --datamodels=tests.input.srh_chatbot.srh_models --tags 3 "menstruation_pregnancy_puberty"
#python main.py create_flows  $srh_content -o ("..\srh-jamaica-chatbot\flows\srh_content_stis.json") --format=google_sheets --datamodels=tests.input.srh_chatbot.srh_models --tags 3 "stis"
#python main.py create_flows  $srh_content -o ("..\srh-jamaica-chatbot\flows\srh_content_contraceptives.json") --format=google_sheets --datamodels=tests.input.srh_chatbot.srh_models --tags 3 "contraceptives"
#python main.py create_flows  $srh_content -o ("..\srh-jamaica-chatbot\flows\srh_content_gender_abstinence_mental_violence_relation.json") --format=google_sheets --datamodels=tests.input.srh_chatbot.srh_models --tags 3 "gender_abstinence_mental_violence_relation"

rpft create_flows  $srh_content -o ("..\srh-jamaica-chatbot\flows\srh_content_menstruation_pregnancy_puberty.json") --format=google_sheets --datamodels=tests.input.srh_chatbot.srh_models --tags 3 "menstruation_pregnancy_puberty"

Set-Location "..\srh-jamaica-chatbot"
Write-Output "created flows"

$source_files = @("srh_registration","srh_entry","srh_content_contraceptives","srh_content_stis","srh_content_menstruation_pregnancy_puberty","srh_content_gender_abstinence_mental_violence_relation")

$source_file_name = $source_file_name + "_no_QR"
$select_phrases_file = ".\edits\select_phrases.json"
$special_words = ".\edits\special_words.json"
$count_threshold = "2"
$length_threshold = "18"
$qr_limit = "10"
#$add_selectors = "yes"

$SPREADSHEET_ID = '1SDUUCbDL1-oW7b9pB2RqfM6HqB-jeLDAdT3Ng6e515I'
$CONFIG_ab = "..\srh-jamaica-chatbot\edits\ab_config.json"

$sg_flow_uuid = "ecbd9a63-0139-4939-8b76-343543eccd94"
$sg_flow_name = "SRH - Safeguarding - WFR interaction"

$default_expiration = 180
$special_expiration = "..\srh-jamaica-chatbot\edits\expiration_times.json"


for ($i=0; $i -lt $source_files.length; $i++) {
    
    $source_file_name = $source_files[$i]
    Write-Output ("processing " + $source_file_name)
    $input_path = ".\flows\" + $source_file_name +".json"

    #step 1: update expiration time
    node ../idems-chatbot-repo/update_expiration_time.js $input_path $special_expiration $default_expiration $input_path
        
    # step 2: flow edits & A/B testing

    $JSON_FILENAME = "..\srh-jamaica-chatbot\flows\" + $source_file_name + ".json"
    $source_file_name = $source_file_name + "_edits" 
    $output_path_2 = "temp\" + $source_file_name + ".json"
    $AB_log = "..\srh-jamaica-chatbot\temp\AB_warnings_" + $source_files[$i] + ".log"
    Set-Location "..\rapidpro_abtesting"
    python main.py $JSON_FILENAME ("..\srh-jamaica-chatbot\" +$output_path_2) $SPREADSHEET_ID --format google_sheets --logfile $AB_log --config=$CONFIG_ab
    Write-Output "added A/B tests and localisation"
    $input_path = $output_path_2
    Set-Location "..\srh-jamaica-chatbot"


    # step 4: add quick replies to message text and translation

    $output_path_4 = ".\temp\"
    $output_name_4 = $source_file_name 


    node ..\idems_translation\chatbot\index.js reformat_quick_replies $input_path $select_phrases_file $output_name_4 $output_path_4 $count_threshold $length_threshold $qr_limit $special_words
    
    
    
    
    Write-Output "Removed quick replies"

    if(-not ($source_file_name -match 'srh_registration')){
    # step 5: safeguarding

    $input_path_5 = $output_path_4 + $output_name_4 +".json"
    $source_file_name = $source_file_name + "_safeguarding"
    $output_path_5 = ".\temp\upload\"+ $source_file_name +".json"
    $safeguarding_path = ".\edits\safeguarding_srh.json"
    node ..\safeguarding-rapidpro\srh_add_safeguarding_to_flows.js $input_path_5 $safeguarding_path $output_path_5 $sg_flow_uuid $sg_flow_name
    Write-Output "Added safeguarding"
    


    node ..\safeguarding-rapidpro\srh_edit_redirect_flow.js $output_path_5 $safeguarding_path $output_path_5
    Write-Output "Edited redirect sg flow"

    <#
    # step final: split in 2 json files because it's too heavy to load (need to replace wrong flow names)
    if($source_file_name -match 'srh_navigation'  ){
    $input_path_6 = $output_path_5 
    $n_file = 4
    node ..\idems-chatbot-repo\split_in_multiple_json_files.js $input_path_6 $n_file

    Write-Output ("Split file in " + $n_file + " parts")
    }

    if($source_file_name -match 'srh_other'  ){
        $input_path_6 = $output_path_5 
        $n_file =2
        node ..\idems-chatbot-repo\split_in_multiple_json_files.js $input_path_6 $n_file
    
        Write-Output ("Split file in " + $n_file + " parts")
        }
    #>
    }

    
    Write-Output (" -------------------- ")
}



