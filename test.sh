curl --location 'https://qa-platform-v4-scan-1-archive.metadefender.com/file' \
--header 'apikey: 8b1b685c22b7ee75e297a70cd4b2bc872c13' \
--header 'rule: File scan' \
--header 'filename: %%D9%82%D8%B1%D8%A7%D8%B1%20%D8%A7%D9%84%D9%85%D8%AD%D9%83%D9%85%D8%A9.rtf' \
--header 'metadata: {"custom_id":"123456","notes":"This is a test file.", "filename": "%D9%82%D8%B1%D8%A7%D8%B1%20%D8%A7%D9%84%D9%85%D8%AD%D9%83%D9%85%D8%A9.rtf"}' \
--form 'file=@"/home/andreidomsa/Downloads/قرار المحكمة.rtf"'