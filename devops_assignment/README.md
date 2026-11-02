# Python Docker CI/CD Assignment

## 1. Project objective

Build a small Python web service, test it automatically with GitHub Actions, package it as a Docker image, publish that image to Docker Hub, and run the published container locally.

**Tools:** Python 3.11, FastAPI, Uvicorn, pytest, Docker, GitHub Actions, and Docker Hub.

## 2. Project structure

```text
devops_assignment/
├── .github/
│   └── workflows/
│       └── ci-cd.yml
├── screenshots/
│   └── (put your assignment screenshots here)
├── tests/
│   └── test_app.py
├── .dockerignore
├── .gitignore
├── app.py
├── main.py
├── Dockerfile
├── README.md
├── DEPLOYMENT_CHECKLIST.md
├── requirements-dev.txt
└── requirements.txt
```

## 3. Application endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Welcome message and service status |
| GET | `/health` | Health-check endpoint |
| GET | `/api/info` | Basic application and runtime information |

The service listens on port `8000` inside the container. Uvicorn runs the FastAPI ASGI application.

## 4. Run and test locally (before GitHub)

Open a terminal in this project directory.

### Create and activate a virtual environment (optional but recommended)

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

This project is configured for Python 3.11 to match a common local development setup. Keep the Python version consistent in the Dockerfile and GitHub Actions workflow if you change it.

### Install and test

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -v
```

Expected result: all 3 tests pass.

### Run without Docker (optional)

```powershell
uvicorn main:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000/` and `http://localhost:8000/health`.

## 5. Build and run the Docker container locally

Make sure Docker Desktop is installed, open, and running.

```powershell
docker build -t devops-python-service:local .
docker run -d --name devops-python-service -p 8000:8000 devops-python-service:local
```

Verify in a browser:

- `http://localhost:8000/`
- `http://localhost:8000/health`
- `http://localhost:8000/api/info`

Check container status and health:

```powershell
docker ps
docker inspect --format='{{.State.Health.Status}}' devops-python-service
```

Stop and remove the local container when finished:

```powershell
docker stop devops-python-service
docker rm devops-python-service
```

## 6. Configure Docker Hub

1. Create or sign in to a Docker Hub account at <https://hub.docker.com/>.
2. Create a **public** repository named `devops-python-service`.
3. In Docker Hub, create a personal access token with the permissions needed to push images. Use the token in GitHub Actions; do not use your Docker Hub account password.
4. Copy your Docker Hub username and token securely.

## 7. Create the GitHub repository

1. Create a new GitHub repository, for example `devops-python-cicd`.
2. Keep the default branch named `main`.
3. Leave the repository empty; do not add a README or `.gitignore` from the GitHub website because this project already contains them.

## 8. Add GitHub Actions secrets

Before the first push, open **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret name | Value |
|---|---|
| `DOCKERHUB_USERNAME` | Your Docker Hub username |
| `DOCKERHUB_TOKEN` | The Docker Hub access token you created |

Do not put the token in this project, README, YAML file, screenshots, or Git commits. Adding secrets before the first push allows the initial publish job to authenticate successfully.

## 9. Push the project and inspect the pipeline

In a terminal opened in this project folder, run:

```powershell
git init
git branch -M main
git add .
git commit -m "Build Python service with Docker CI/CD"
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/devops-python-cicd.git
git push -u origin main
```

Replace `YOUR_GITHUB_USERNAME` with your GitHub username. If Git says that `origin` already exists, use `git remote set-url origin https://github.com/YOUR_GITHUB_USERNAME/devops-python-cicd.git` instead.

The workflow is stored at `.github/workflows/ci-cd.yml`.

- A push to `main` runs the CI test job and, if tests pass, the CD image-publishing job.
- A pull request targeting `main` runs CI tests. It does not publish an image.
- The published Docker Hub tags are `latest` and the full Git commit SHA.

Open the repository's **Actions** tab. Select **Python Docker CI-CD** and open the latest run. Confirm that both `test` and `publish` jobs succeed.

## 10. Pull and run the published image

After the publish job succeeds, open Docker Hub and confirm that the repository has image tags. Then run these commands on your computer (replace `YOUR_DOCKERHUB_USERNAME`):

```powershell
docker pull YOUR_DOCKERHUB_USERNAME/devops-python-service:latest
docker run -d --name devops-python-service -p 8000:8000 YOUR_DOCKERHUB_USERNAME/devops-python-service:latest
```

Open the same three URLs from section 5 and confirm the service responds. Use `docker ps` to show that the container is running.

If a container with that name already exists, stop and remove it before running the new one:

```powershell
docker stop devops-python-service
docker rm devops-python-service
```

## 11. CI/CD flow

```text
Developer pushes code to GitHub main
                |
                v
       GitHub Actions starts
                |
                v
     Install Python dependencies
                |
                v
       Run pytest automated tests
                |
        Tests pass? ---- No ---> Pipeline fails; no image is published
                |
               Yes
                |
                v
        Build Docker image
                |
                v
        Authenticate to Docker Hub
                |
                v
      Push latest + commit-SHA tags
                |
                v
   Pull image and run container locally
                |
                v
      Verify service and health endpoint
```

## 12. What counts as deployment in this assignment?

This pipeline deploys/publishes the built container image to Docker Hub. You then pull and run that exact published image as a Docker container on your computer. This demonstrates automated build and image delivery plus a running container. It does **not** provision a public cloud VM or expose the service to the public internet; that would be an additional hosting step.

## 13. Troubleshooting

- **Docker daemon not running:** Start Docker Desktop and wait until it reports that Docker is running.
- **Port 8000 already in use:** Run the container with `-p 8001:8000` and open `http://localhost:8001/`.
- **Docker Hub login/push fails:** Verify the two GitHub secret names and values. Use a Docker Hub access token, not your account password.
- **Publish job is skipped:** Confirm that the commit was pushed to the `main` branch. Pull requests intentionally do not publish.
- **Image not found:** Confirm the publish job succeeded and the Docker Hub repository name is exactly `devops-python-service`.
- **Container exits:** Run `docker logs devops-python-service` to inspect the error.

## 14. Evidence to capture for submission

See `DEPLOYMENT_CHECKLIST.md` for the screenshot checklist. Capture genuine screenshots from your own GitHub, Docker Hub, terminal, and browser. Do not include access tokens or passwords.
