set dotenv-filename := x"${JUST_ENV:-.env}"
set dotenv-load
set dotenv-override

WORKSPACE := env_var_or_default("WORKSPACE", justfile_directory())

serve:
  uv run ./langflowx/main.py run --components-path {{WORKSPACE}}/components --env-file {{WORKSPACE}}/.env
