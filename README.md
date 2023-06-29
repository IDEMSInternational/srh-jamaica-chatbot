# SRH Jamaica RapidPro flow authoring pipeline

This project builds RapidPro flows for the SRH Jamaica chatbot. It takes input from specific Google Sheets spreadsheets and produces RapidPro flow JSON files that are ready to upload to any RapidPro server.

# Usage

The pipeline is intended to be run by triggering a Github Actions workflow.

1. Navigate to the page for the [Produce RapidPro Flows][1] action
1. Click on the _Run workflow_ button; a drop-down will appear
1. Make sure _Branch_ is set to _main_
1. Click on the green _Run workflow_ button

# Development

These steps only need to be followed if you want to develop the pipeline.

## Setup

1. Install Python >= 3.6
1. Create a Python virtual environment `python -m venv .venv`
1. Activate the environment `source .venv/bin/activate`
1. Upgrade pip `pip install --upgrade pip`
1. Install project Python dependencies `pip install -r requirements.txt`
1. Install latest Node and NPM Long-Term Support (LTS) versions
1. Install project Node dependencies `npm install`

## Run

The script srh_jamaica.py contains the full process to produce RapidPro flows from the relevant Google Sheets.

To run the script:
```
python srh_jamaica.py
```


[1]: https://github.com/IDEMSInternational/srh-jamaica-chatbot/actions/workflows/main.yml
