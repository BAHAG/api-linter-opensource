provider "google" {
  project = var.project
  region  = var.region
  zone    = var.zone
}

terraform {
  required_version = ">= 0.14"

  required_providers {
    # Cloud Run support was added on 3.3.0
    google = ">= 3.3"
  }
  backend "gcs" {
  }
}