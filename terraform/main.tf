resource "google_storage_bucket" "linter_binary" {
  name          = var.bucket_name
  location      = "EU"
  force_destroy = true

  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
}


resource "google_storage_bucket_object" "picture" {
  name   = "mac-binary"
  source = "../mac_dist.tar.gz"
  bucket = google_storage_bucket.linter_binary.name
}

# resource "google_storage_default_object_access_control" "linter_binary_all_access" {
#   bucket = google_storage_bucket.linter_binary.name
#   role   = "READER"
#   entity = "group-b2b-gcp-users@bahag.com"
# }

# add all users as viewers for the bucket
resource "google_storage_bucket_iam_member" "all_teams_linter_binary" {
  bucket = google_storage_bucket.linter_binary.name
  role   = "roles/storage.objectViewer"
  member = "group:b2b-gcp-users@bahag.com"
}

resource "google_storage_bucket" "vs_extension_dir" {
  name          = var.extension_name
  location      = "EU"
  force_destroy = true

  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
}

# add all users as viewers for the bucket
resource "google_storage_bucket_iam_member" "all_teams_linter_vscode_extension" {
  bucket = google_storage_bucket.vs_extension_dir.name
  role   = "roles/storage.objectViewer"
  member = "group:b2b-gcp-users@bahag.com"
}

resource "google_storage_bucket_object" "vs_extension" {
  name   = "vs_extension.vsix"
  source = "../api_linter_extension.vsix"
  bucket = google_storage_bucket.vs_extension_dir.name
}

# resource "google_storage_default_object_access_control" "vs_extension_all_access" {
#   bucket = google_storage_bucket.vs_extension_dir.name
#   role   = "READER"
#   entity = "group-b2b-gcp-users@bahag.com"
# }