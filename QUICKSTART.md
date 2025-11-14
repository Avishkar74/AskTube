# AskTube Quick Start Guide

Get up and running with AskTube in 5 minutes!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Set Up API Key

Create a `.env` file in the project root:

```bash
echo "GOOGLE_API_KEY=your_api_key_here" > .env
```

Get your Gemini API key: https://makersuite.google.com/app/apikey

## Step 3: Run Your First Video

```bash
python asktube.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

## Step 4: View Your Outputs

Check the `outputs/` directory for:
- Summary (`.txt`)
- Study Notes (`.md` and `.json`)
- Mind Map (`.mmd`)

## Next Steps

### Process a Transcript File

```bash
python asktube.py --transcript my_transcript.txt
```

### Skip Certain Outputs

```bash
python asktube.py URL --skip-mindmap
```

### Disable Caching

```bash
python asktube.py URL --no-cache
```

### View All Options

```bash
python asktube.py --help
```

## Example Outputs

Check `outputs/example_*` files to see what AskTube generates!

## Troubleshooting

### No API Key Error
Make sure your `.env` file exists and contains `GOOGLE_API_KEY=...`

### Transcript Not Available
Use `--transcript` to manually provide the transcript text.

### Rate Limiting
The tool handles this automatically. Just wait for the retries to complete.

## Full Documentation

See [README.md](README.md) for complete documentation.
