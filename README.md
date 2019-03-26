QMUL coursework 2019
Mini project to demonstrate Python Flask etc
Serve as a wrapper to public Pokemon API

APIs:
  - '/pokemon', methods=['GET']
  Get information about all pokemons

    Query parameters:
      - auth_token [Required] -- auth token for the user making the request
      - offset [Optional] -- offset index of result, default: 0
      - limit [Optional] -- size of the return result page, default: 20

    Successful response [200 OK]:
      - count -- total number of results
      - next -- URL for next page of results
      - previous -- URL for previous page of results
      - results -- Array of pokemon names and URLs
        - name -- name of pokemon
        - url -- URL for details of the specific pokemons

    
  - '/user', methods=['POST']
  Register a user

    Payload parameters:
      - username [Required]
      - password [Required]
      - email [Required]

    Successful response [201 Created]:
      - <intentionally empty body>

    Unsuccessful response [409 Conflict]：
      - error -- error message

  - '/user', methods=['PUT']
  Change a user's password

    Payload parameters:
      - auth_token [Required] -- auth token for the user under change
      - new_password [Required]

    Successful response [200 OK]:
      - auth_token -- new auth token for the user making the request
    
    
  - '/user/<username>', methods=['DELETE']
  Delete a user

    Path parameters:
      - username

    Query parameters:
      - auth_token [Required] -- auth token for the user making the request

    Successful response [200 OK]:
      - <intentionally empty body>


  - '/login', methods=['POST']
  Login a user

    Payload parameters:
      - username [Required]
      - password [Required]

    Successful response [200 OK]:
      - auth_token -- auth token for the user making the request
