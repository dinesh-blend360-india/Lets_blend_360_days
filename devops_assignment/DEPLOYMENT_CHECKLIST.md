# Execution and Screenshot Checklist

Use this file while completing the assignment. Tick each item as you finish it.

## A. Local application and tests

- [ ] Open the `devops_assignment` folder in VS Code.
- [ ] Confirm Python 3.11 is available.
- [ ] Install dependencies using `python -m pip install -r requirements-dev.txt`.
- [ ] Run `python -m pytest -v` and confirm all 3 tests pass.
- [ ] Install/start Docker Desktop.
- [ ] Build the image with `docker build -t devops-python-service:local .`.
- [ ] Start the local container and verify `/`, `/health`, and `/api/info`.

## B. GitHub and Docker Hub setup

- [ ] Create a Docker Hub public repository named `devops-python-service`.
- [ ] Create a Docker Hub access token.
- [ ] Create a GitHub repository with default branch `main`.
- [ ] Add `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` under GitHub Actions repository secrets before the first push.
- [ ] Push this complete project to GitHub.

## C. Pipeline and image publication

- [ ] Open the GitHub repository Actions tab.
- [ ] Confirm the CI test job succeeds.
- [ ] Confirm the CD publish job succeeds.
- [ ] Open Docker Hub and confirm the `latest` and commit-SHA image tags exist.
- [ ] Pull the Docker Hub image locally.
- [ ] Run the pulled image as a container.
- [ ] Confirm all three endpoints respond successfully.
- [ ] Confirm `docker ps` shows the running container.

## D. Screenshots to send for the final report

Capture screenshots with the relevant page or command clearly visible. Number them in this order if possible:

1. **Project structure in VS Code** — show the app, Dockerfile, tests, and `.github/workflows/ci-cd.yml`.
2. **Local test results** — terminal showing all pytest tests passed.
3. **Docker image build** — terminal showing the successful `docker build` command.
4. **Local container running** — `docker ps` showing `devops-python-service` and port mapping.
5. **Application home endpoint** — browser at `http://localhost:8000/`.
6. **Health endpoint** — browser at `http://localhost:8000/health`.
7. **GitHub repository** — project files visible in the repository.
8. **GitHub Actions workflow success** — both `test` and `publish` jobs green.
9. **Docker Hub repository/tags** — `latest` and the SHA tag visible. Do not show access tokens.
10. **Pulled image running** — terminal showing `docker pull`, `docker run`, and/or `docker ps` for the published image.

Optional: include `/api/info` if you want one more endpoint screenshot.

## E. Before sharing screenshots

- [ ] Check that no passwords, Docker Hub tokens, `.env` files, or private credentials are visible.
- [ ] Share screenshots in this chat. They can be sent in multiple messages.
- [ ] Tell me when all screenshots have been sent; I will prepare the final submission document using your actual evidence.
