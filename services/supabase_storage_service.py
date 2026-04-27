# # supabase_client.py
# from supabase import create_client
# import os

# supabase = create_client(
#     os.getenv("SUPABASE_URL"),
#     os.getenv("SUPABASE_KEY")
# )


# def upload_mri_file(file, patient_id, label):
#     path = f"mri/{patient_id}/{label}.nii.gz"

#     file.seek(0)
#     content = file.read()

#     supabase.storage.from_("mri").upload(
#         path,
#         content,
#         file_options={"content-type": "application/octet-stream", "upsert": "true"}
#     )

#     url = supabase.storage.from_("mri").get_public_url(path)

#     return url, path


# def delete_mri_file(path):
#     supabase.storage.from_("mri").remove([path])