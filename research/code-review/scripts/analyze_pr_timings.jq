# Calculate time differences in hours
def time_diff_hours(from; to):
  if from and to then
    ((to | fromdateiso8601) - (from | fromdateiso8601)) / 3600
  else
    null
  end;

# Calculate time differences in days
def time_diff_days(from; to):
  if from and to then
    ((to | fromdateiso8601) - (from | fromdateiso8601)) / 86400
  else
    null
  end;

# Process each PR
{
  repo,
  number,
  created: .createdAt,
  merged: .mergedAt,
  first_review: (.reviews[0].submittedAt // null),
  review_count: (.reviews | length),
  time_to_first_review_hours: time_diff_hours(.createdAt; .reviews[0].submittedAt // null),
  time_to_first_review_days: time_diff_days(.createdAt; .reviews[0].submittedAt // null),
  time_to_merge_hours: time_diff_hours(.createdAt; .mergedAt),
  time_to_merge_days: time_diff_days(.createdAt; .mergedAt)
}
