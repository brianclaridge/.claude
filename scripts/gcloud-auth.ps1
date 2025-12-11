#!/usr/bin/env pwsh
param (
  [Parameter()]
  [switch]
  $add_gmedia_bucket_policy
)

gcloud auth application-default set-quota-project ${env:GOOGLE_CLOUD_PROJECT}
gcloud config set project ${env:GOOGLE_CLOUD_PROJECT}
gcloud auth login --update-adc --no-launch-browser

if ($add_gmedia_bucket_policy) {
  gcloud auth application-default set-quota-project ${env:GOOGLE_CLOUD_PROJECT}
  gcloud storage buckets add-iam-policy-binding gs://${env:GENMEDIA_BUCKET} `
    --member=user:${env:GCLOUD_EMAIL_ADDRESS} `
    --role=roles/storage.objectUser
}
