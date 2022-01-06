<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/html" lang="ru">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="robots" content="noindex, nofollow">
    <link href="/css/bootstrap.min.css" rel="stylesheet">
    <link href="/css/style.css" rel="stylesheet">
    <script src="/js/bootstrap.min.js"></script>
    <title>{{ page_title }}</title>
  </head>
  <body class="text-center">
    <main class="form-change-password">
      <h3 class="mb-3">{{ page_title }}</h3>
      %for type, text in get('alerts', []):
          <div class="alert alert-{{ type }} alert-dismissible fade show" role="alert">
            {{ text }}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Скрыть"></button>
          </div>
      %end
      <form method="post">
        <div class="form-floating mb-3">
          <input id="username" class="form-control" name="username" value="{{ get('username', '') }}" type="text" placeholder="username" required autofocus>
          <label for="username" class="form-label">{{ text_username }}</label>
        </div>
        <div class="form-floating mb-3">
          <input id="old-password" class="form-control" name="old-password" type="password" placeholder="Пароль" required>
          <label for="old-password" class="form-label">{{ text_old_password }}</label>
        </div>
        <div class="form-floating mb-3">
          <input id="new-password" class="form-control" name="new-password" type="password" placeholder="Новый пароль" required>
          <label for="new-password" class="form-label">{{ text_new_password }}</label>
        </div>
        <div class="form-floating mb-3">
          <input id="confirm-password" class="form-control" name="confirm-password" type="password" placeholder="Подтверждение нового пароля" required>
          <label for="confirm-password" class="form-label">{{ text_new_password_confirmation }}</label>
        </div>
        <button type="submit" class="btn btn-primary">{{ text_update_password }}</button>
      </form>
    </main>
  </body>
</html>