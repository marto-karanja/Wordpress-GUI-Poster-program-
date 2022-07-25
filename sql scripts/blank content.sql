SELECT * FROM crawls.coursehero_content;
select count(*) from coursehero_content where content_length=0 union select count(*) from coursehero_content where content_length > 0