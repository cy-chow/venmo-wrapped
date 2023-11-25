# Venmo Wrapped - CSE 291 Research Project 

### Carl Chow, Eric Xiao, Kyeling Ong, Nachelle Matute

A script that extracts personal information from social networks on Venmo.

## Getting Started
To install dependencies, run `pip install -r requirements.txt`. 

This script also requires a separate `access_token.txt` file in the same directory as the script, 
which contains a Venmo account access token, in order to make authenticated API requests.

A more detailed overview of how to generate an access token for your user account
can be found at the [Venmo API Github](https://github.com/mmohades/venmo).

## Example Usage

Once you have your account access token, running 

```bash
python wrapped_venmo.py -u <username>
```

runs the user analysis for the user account \<username\>. 
Run `python wrapped_venmo.py -h` for usage information.


## Additional Features

Our group incorporated [SENMO](https://github.com/STEELISI/SENMO), a large language model
that detects sensitive content from Venmo captions, into the final version of
Venmo Wrapped. 

Due to privacy concerns, the updated Python Notebook and our supporting 
documentation is available upon request. 
