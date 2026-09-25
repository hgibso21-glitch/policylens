# Deploying PolicyLens to OpenShift

This deploys the container to the free **Red Hat Developer Sandbox**, which is a real OpenShift cluster. Nothing here needs a paid account.

## How the pieces fit

```text
git push -> GitHub Actions (CI) -> merge to main
                                      |
                       Run "Deploy to OpenShift" (manual)
                                      |
      build image -> push to ghcr.io -> oc login -> oc apply -k deploy/openshift
                                                          |
                              Deployment + Service + Route (HTTPS URL)
```

## One-time setup

1. **Get a sandbox.** Sign up at <https://developers.redhat.com/developer-sandbox> and open the web console.
2. **Find your login command.** In the console, click your name (top right), then **Copy login command**, then **Display Token**. Note the `--server=` URL and the token.
3. **Find your namespace.** It is your project name, shown in the console (usually `<username>-dev`).
4. **Push the repo to GitHub.** Replace `OWNER` in `README.md` and `deploy/openshift/kustomization.yaml` with your GitHub username.
5. **Add GitHub secrets and a variable** (repo Settings, Secrets and variables, Actions):

   | Kind | Name | Value |
   |---|---|---|
   | Secret | `OPENSHIFT_SERVER` | The `--server=` URL |
   | Secret | `OPENSHIFT_TOKEN` | The token |
   | Variable | `OPENSHIFT_NAMESPACE` | Your project name |

   The sandbox token expires after about a day, so refresh the `OPENSHIFT_TOKEN` secret before each deploy. A production pipeline would use a service account instead.
6. **Make the image pullable.** After the first push, open the package on GitHub (your profile, Packages, `policylens`), then Package settings, and set visibility to **Public**. This keeps the demo simple because no image pull secret is needed.
7. **Optional approval gate.** Create an environment named `openshift` in repo Settings and add yourself as a required reviewer.

## Deploy

GitHub, Actions, **Deploy to OpenShift**, **Run workflow**. When it finishes, the last step prints the URL. Open it and add `/docs`.

## Deploy by hand (to understand what the workflow does)

```bash
oc login --token=<token> --server=<server>
oc project <namespace>
# edit newName in deploy/openshift/kustomization.yaml to your image
oc apply -k deploy/openshift
oc rollout status deployment/policylens
oc get route policylens
```

## Useful commands

| Goal | Command |
|---|---|
| See pods | `oc get pods` |
| Read logs | `oc logs deployment/policylens` |
| Why did a pod not start | `oc describe pod -l app.kubernetes.io/name=policylens` |
| Which security context was applied | `oc get pod -l app.kubernetes.io/name=policylens -o yaml` and look for `openshift.io/scc` |
| Remove everything | `oc delete -k deploy/openshift` |

## Why the manifests look the way they do

| Setting | Reason |
|---|---|
| No `runAsUser`, `runAsNonRoot: true` | OpenShift's **restricted-v2** policy assigns a random user id from the namespace range. Pinning a user id would be rejected. |
| Dockerfile gives group 0 write access to `/data` | The random user always belongs to group 0, so that is how it can write the SQLite file. |
| Port 8080 | Non-root processes cannot bind ports below 1024. |
| `emptyDir` volume | The demo database is disposable. It resets when the pod restarts, and `SEED_MOCK_DATA` reloads the mock data. |
| One replica | A SQLite file cannot be shared between pods. A real deployment would use PostgreSQL. |
| `/healthz` and `/readyz` probes | Liveness restarts a hung process. Readiness keeps traffic away until the database answers. |

`tests/test_manifests.py` checks these settings on every CI run.

## Troubleshooting

- **`ImagePullBackOff`:** the package is still private, or `newName` does not match the pushed image.
- **`CrashLoopBackOff` with a permission error:** something is writing outside `/data`.
- **Pod rejected by a security policy:** someone added `runAsUser`, a privileged setting or a port below 1024. `tests/test_manifests.py` should have caught it.
- **Route works but `/rulesets` is empty:** `SEED_MOCK_DATA` is not `"true"` in the ConfigMap, or the pod restarted before the app finished starting.
