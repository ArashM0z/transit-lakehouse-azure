# Argo CD configuration

GitOps for the transit-lakehouse platform — Argo CD watches `main` and reconciles cluster state to match what is committed.

## Layout

```
argocd/
├── projects/                       # AppProject CRDs
│   └── transit-lakehouse.yaml      # umbrella project (sources, dests, RBAC)
└── applications/                   # Application + Rollout CRDs
    ├── scoring-api-dev.yaml        # auto-sync to dev namespace
    ├── scoring-api-prod.yaml       # manual sync, prod namespace
    └── scoring-api-rollout.yaml    # Argo Rollouts canary with Prometheus analysis
```

## Bootstrap

```bash
# install Argo CD via Helm (assumes kubeconfig points at the cluster)
helm repo add argo https://argoproj.github.io/argo-helm
helm install argocd argo/argo-cd -n argocd --create-namespace -f helm/argocd/values.yaml

# install Argo Rollouts
helm install argo-rollouts argo/argo-rollouts -n argo-rollouts --create-namespace

# register this repo + bootstrap the project and apps
kubectl apply -f argocd/projects/transit-lakehouse.yaml
kubectl apply -f argocd/applications/scoring-api-dev.yaml
kubectl apply -f argocd/applications/scoring-api-prod.yaml
```

## Promotion flow

1. Merge to `main` → CI builds, scans, signs, and pushes the image to GHCR.
2. Argo CD detects the Helm chart change and auto-syncs `scoring-api-dev`.
3. After eyeballing the dev environment, a maintainer clicks **Sync** on `scoring-api-prod`.
4. Argo Rollouts walks the canary: 5% → analysis → 25% → analysis → 50% → 100%, with auto-rollback if `forecast-latency-p95` or `forecast-error-rate` analyses fail.

## Notifications

The Argo CD Notifications controller fires Slack messages on:
- `on-sync-failed`
- `on-health-degraded`
- `on-deployed`

Templates and triggers live in `helm/argocd/values.yaml`.
 ## Reconciliation cadence  Argo CD polls every 3 minutes by default. Webhook-driven sync (configured in `helm/argocd/values.yaml`) cuts this to near-real-time for the dev environment.

## See also
