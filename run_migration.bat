@echo off
echo ========================================
echo Smart Athlete - Database Migration
echo ========================================
echo.
echo This will add the profile_picture column to the database.
echo.
echo IMPORTANT: If asked about renaming a field, answer 'n' (no)
echo.
pause

cd backend
echo.
echo Running migrations...
echo.
python manage.py migrate

echo.
echo ========================================
echo Migration Complete!
echo ========================================
echo.
echo You can now start the server with:
echo python manage.py runserver
echo.
pause
