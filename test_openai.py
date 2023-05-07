import openai
import pandas as pd

# Set up API key
openai.api_key = "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"

# Load market data
#market_data = pd.read_csv("market_data.csv")

# Generate prompts
prompts = [
    "Is TSLA a good stock?"
#    "What is the trend in the market?",
#    "What is the best stock to buy?",
#    "What is the best time to sell my stock?",
]

# Generate responses
for prompt in prompts:
    response = openai.Completion.create(
        engine="davinci",
        prompt=prompt,
        max_tokens=100,
        n=1,
        stop=None,
        temperature=0.5,
    )

    # Print response
    #print(response.choices[0].text)
    print(response)

