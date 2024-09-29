import logging
from dataFetchFunctions import CAMarksWebScrapper
from dataExceptions import InvalidUsernameOrPasswordException, ScrappingError, NoSemResultsAvailable, NoCAMarksAvailable, AttendanceUpdateInProcessException, NoTimeTableDataException

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def print_data(data, title):
    print(f"\n{title}:")
    print("-" * len(title))
    print(data)

def main(username, password):
    try:
        scraper = CAMarksWebScrapper(user_name=username, password=password)

        # Fetch and print student profile
        profile = scraper.fetch_student_profile()
        print_data(profile, "Student Profile")

        # Fetch and print attendance
        attendance = scraper.fetch_attendance()
        print_data(attendance, "Attendance")

        # # Fetch and print timetable
        # timetable = scraper.fetch_time_table()
        # print_data(timetable, "Timetable")

        # Fetch and print current semester exam results
        current_sem_results = scraper.fetch_current_sem_exam_results()
        print_data(current_sem_results, "Current Semester Results")

        # Fetch and print all previous semester results
        previous_sem_results = scraper.fetch_all_previous_semester_exam_results()
        print_data(previous_sem_results, "Previous Semester Results")

        # Fetch and print CA marks
        ca_marks_1, ca_marks_2 = scraper.fetch_ca_marks()
        print_data({"CA Marks 1": ca_marks_1, "CA Marks 2": ca_marks_2}, "CA Marks")

        # # Fetch and print test timetable
        # test_timetable = scraper.fetch_test_timetable()
        # print_data(test_timetable, "Test Timetable")

    except InvalidUsernameOrPasswordException:
        logging.error("Invalid username or password")
    except ScrappingError as e:
        logging.error(f"An error occurred while scraping data: {str(e)}")
    except NoSemResultsAvailable:
        logging.warning("No semester results available")
    except NoCAMarksAvailable:
        logging.warning("No CA marks available")
    except AttendanceUpdateInProcessException:
        logging.info("Attendance update is in process")
    except NoTimeTableDataException:
        logging.warning("No timetable data available")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    username = "22z209"
    password = "06MAY04"
    main(username, password)