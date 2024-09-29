import requests
import re
import math
from bs4 import BeautifulSoup
from typing import List,Dict
import logging


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

from dataModels import CAMarksModel, AttendanceModel, TimeTableModel, SemMarkModel
from dataExceptions import InvalidUsernameOrPasswordException, ScrappingError, NoSemResultsAvailable, NoCAMarksAvailable, AttendanceUpdateInProcessException, NoTimeTableDataException



class CAMarksWebScrapper:
    ECAMPUS_URL = "https://ecampus.psgtech.ac.in/studzone2/"
    STUDENT_PROFILE_PAGE_URL = "https://ecampus.psgtech.ac.in/studzone2/AttWfStudProfile.aspx"
    ATTENDANCE_PAGE_URL = "https://ecampus.psgtech.ac.in/studzone2/AttWfPercView.aspx"
    TIMETABLE_PAGE_URL = "https://ecampus.psgtech.ac.in/studzone2/AttWfStudTimtab.aspx"
    SEM_EXAM_RESULTS_PAGE_URL = (
        "https://ecampus.psgtech.ac.in/studzone2/FrmEpsStudResult.aspx"
    )
    COURSE_DETAILS_PAGE_URL = (
        "https://ecampus.psgtech.ac.in/studzone2/AttWfStudCourseSelection.aspx"
    )
    CA_MARKS_URL="https://ecampus.psgtech.ac.in/studzone2/CAMarks_View.aspx"
    TEST_TIME_TABLE_URL = "https://ecampus.psgtech.ac.in/studzone2/FrmEpsTestTimetable.aspx"

    def __init__(self, user_name, password):
        self.session = requests.Session()
        login_page = self.session.get(self.ECAMPUS_URL)
        soup = BeautifulSoup(login_page.text, "html.parser")
        item_request_body = self.generate_login_request_body(soup, user_name, password)
        response = self.session.post(
            url=login_page.url,
            data=item_request_body,
            headers={"Referer": login_page.url},
        )

        if response.status_code != 200:
            raise ScrappingError
        soup = BeautifulSoup(response.text, "html.parser")
        message = soup.find(string=re.compile("Invalid"))
        if message and "Invalid" in message:
            raise InvalidUsernameOrPasswordException

    def convert_data_to_json(self):
        pass

    @staticmethod
    def grade_score(grade: str) -> int:
        grades = {
            "O": 10,
            "A+": 9,
            "A": 8,
            "B+": 7,
            "B": 6,
            "C+": 5,
            "C": 4,
            "W": 0,
            "RA": 0,
            "SA": 0,
        }
        return grades.get(grade, 0)

    @staticmethod
    def apply_the_bunker_formula(
        percentage_of_attendance: int,
        total_hours: int,
        total_present: int,
        threshold=0.75,
    ) -> dict:
        res = {}
        if percentage_of_attendance <= 75:
            res["class_to_attend"] = math.ceil(
                (threshold * total_hours - total_present) / (1 - threshold)
            )
        else:
            res["class_to_bunk"] = math.floor(
                (total_present - (threshold * total_hours)) / (threshold)
            )
        return res

    @staticmethod
    def generate_login_request_body(
        soup: BeautifulSoup, user_name: str, password: str
    ) -> dict:
        view_state = soup.select("#__VIEWSTATE")[0]["value"]
        event_validation = soup.select("#__EVENTVALIDATION")[0]["value"]
        view_state_gen = soup.select("#__VIEWSTATEGENERATOR")[0]["value"]

        item_request_body = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__LASTFOCUS": "",
            "__VIEWSTATE": view_state,
            "__VIEWSTATEGENERATOR": view_state_gen,
            "__EVENTVALIDATION": event_validation,
            "rdolst": "S",
            "txtusercheck": user_name,
            "txtpwdcheck": password,
            "abcd3": "Login",
        }
        return item_request_body

    @staticmethod
    def parse_table_data_as_attendance_models(data: list) -> List[AttendanceModel]:
        return [
            AttendanceModel(
                course_code=d[0],
                total_hours=int(d[1]),
                exemption_hours=int(d[2]),
                total_absent=int(d[3]),
                total_present=int(d[4]),
                percentage_of_attendance=int(d[5]),
                percentage_with_exemp=int(d[6]),
                percentage_with_exemp_med=int(d[7]),
                attendance_percentage_from=d[8],
                attendance_percentage_to=d[9],
                remark=CAMarksWebScrapper.apply_the_bunker_formula(
                    percentage_of_attendance=int(d[5]),
                    total_hours=int(d[1]),
                    total_present=int(d[4]),
                ),
            )
            for d in data[1:]
        ]



    @staticmethod
    def parse_table_data_as_ca_marks_models(data: list) -> List[CAMarksModel]:
        parsed_data = []
        for d in data[2:]:
            if len(d) >= 10:
                # Replace '*' with None for fields expecting numeric values
                for i in [ 2, 3, 4, 5, 6, 7, 8, 9]:
                    if d[i] == '*':
                        d[i] = '0'

                parsed_data.append(
                    CAMarksModel(
                        courseCode=d[0],
                        courseTitle=d[1],
                        ca1=d[2],
                        ca2=d[3],
                        ca3=d[4],
                        bestOfCA=d[5],
                        at1=d[6],
                        at2=d[7],
                        ap=d[8],
                        total=d[9]
                    )
                )
            else:
                print(d)
                parsed_data.append(
                    CAMarksModel(
                        courseCode=d[0],
                        courseTitle=d[1],
                        ca1=d[2],
                        ca2=d[3],
                        ca3=d[4],
                        bestOfCA=d[5],
                        at1=d[6],
                        at2=d[7],
                        ap=d[8],
                        total='0'
                    )
                )
                # Handle the case where the list doesn't have enough elements
                print(f"Warning: Insufficient data for {d[0]} - {d[1]}")

        return parsed_data


    @staticmethod
    def parse_table_data_as_timetable_models(data: list) -> List[TimeTableModel]:
        return [
            TimeTableModel(
                course_code=d[0], course_title=d[1], programme=d[2], sem_no=d[3]
            )
            for d in data[1:]
        ]

    @staticmethod
    def parse_sem_marks(data: list) -> SemMarkModel:
        CUM_GRADE_X_CREDIT = 0
        CUM_CREDIT = 0
        for d in data[1:]:
            GRADE, CREDIT = CAMarksWebScrapper.grade_score(d[6]), int(d[7])
            CUM_GRADE_X_CREDIT += GRADE * CREDIT
            CUM_CREDIT += CREDIT
        return SemMarkModel(
            latest_sem_no=data[1][4],
            latest_sem_cgpa=round(CUM_GRADE_X_CREDIT / CUM_CREDIT, 3),
        )

    @staticmethod
    def parse_table(table: BeautifulSoup) -> list:
        data = []
        rows = table.find_all("tr")
        for index, row in enumerate(rows):
            cols = row.find_all("td")
            cols = [ele.text.strip() for ele in cols]
            data.append([ele for ele in cols if ele])
        return data

    def fetch_attendance(self):
        attendance_page = self.session.get(self.ATTENDANCE_PAGE_URL)
        soup = BeautifulSoup(attendance_page.text, "html.parser")
        table = soup.find("table", attrs={"class": "cssbody"})
        if table is None:
            message = str(soup.find("span", attrs={"id": "Message"}))
            if "On Process" in message:
                raise AttendanceUpdateInProcessException

        return CAMarksWebScrapper.parse_table_data_as_attendance_models(
            self.parse_table(table)
        )

    def fetch_time_table(self) -> List[TimeTableModel]:
        time_table_page = self.session.get(self.TIMETABLE_PAGE_URL)
        soup = BeautifulSoup(time_table_page.text, "html.parser")
        table = soup.find("table", attrs={"id": "TbCourDesc"})
        if table is None:
            raise NoTimeTableDataException

        return CAMarksWebScrapper.parse_table_data_as_timetable_models(
            self.parse_table(table)
        )

    def fetch_current_sem_exam_results(self):
        sem_exam_results_page = self.session.get(self.SEM_EXAM_RESULTS_PAGE_URL)
        soup = BeautifulSoup(sem_exam_results_page.text, "html.parser")
        table = soup.find("table", attrs={"id": "DgResult"})
        if table is None:
            raise NoSemResultsAvailable

        return self.parse_table(table)

    def fetch_all_previous_semester_exam_results(self):
        course_details_page = self.session.get(self.COURSE_DETAILS_PAGE_URL)
        soup = BeautifulSoup(course_details_page.text, "html.parser")
        table = soup.find("table", attrs={"id": "PDGCourse"})
        if table is None:
            raise ScrappingError

        return CAMarksWebScrapper.parse_sem_marks(self.parse_table(table))


    def fetch_previous_semester_exam_results(self):
        pass
    def fetch_student_profile(self):
        profile_page = self.session.get(self.STUDENT_PROFILE_PAGE_URL)
        if profile_page is None or profile_page.status_code != 200:
            raise ScrappingError(f"Failed to fetch student profile page. Status code: {profile_page.status_code if profile_page else 'None'}")
        
        soup = BeautifulSoup(profile_page.text, "html.parser")
        
        profile_data = {}
        
        # Extract information from the academic details table
        academic_table = soup.find('table', {'id': 'ItStud'})
        if academic_table:
            rows = academic_table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 6:
                    profile_data[cols[0].text.strip().lower()] = cols[2].text.strip()
                    profile_data[cols[3].text.strip().lower()] = cols[5].text.strip()
        
        # Extract address and contact information
        address_table = soup.find('table', {'id': 'DlsAddr'})
        if address_table:
            address_text = address_table.get_text(separator='\n', strip=True)
            
            # Parse address
            address_parts = address_text.split('\n')
            
            # Separate father's name from address
            profile_data['father_name'] = address_parts[0].strip()
            profile_data['address'] = ', '.join(address_parts[1:5]).strip()
            
            # Parse contact information
            contact_info = '\n'.join(address_parts[5:])
            
            contact_patterns = {
                'parent_mobile': r'Mobile:(.+)',
                'parent_email': r'Mail :(.+)',
                'student_mobile': r'Student Mobile:(.+)',
                'student_email': r'Student EMail :(.+)'
            }
            
            for key, pattern in contact_patterns.items():
                match = re.search(pattern, contact_info)
                profile_data[key] = match.group(1).strip() if match else ''
        
        # Clean up and format the data
        formatted_profile = {
            "Personal Information": {
                "Name": profile_data.get('name', ''),
                "Roll Number": profile_data.get('rollno', ''),
                "Batch": profile_data.get('batch', ''),
                "Programme": profile_data.get('programme', ''),
                "Resident Status": profile_data.get('resident-status', '')
            },
            "Family Information": {
                "Father's Name": profile_data.get('father_name', '')
            },
            "Contact Information": {
                "Student Mobile": profile_data.get('student_mobile', ''),
                "Student Email": profile_data.get('student_email', ''),
                "Parent Mobile": profile_data.get('parent_mobile', ''),
                "Parent Email": profile_data.get('parent_email', '')
            },
            "Address": profile_data.get('address', '')
        }
        
        return formatted_profile
    
    
    def fetch_all_previous_semester_exam_results(self):
        course_details_page = self.session.get(self.COURSE_DETAILS_PAGE_URL)
        if course_details_page is None or course_details_page.status_code != 200:
            raise ScrappingError("Failed to fetch course details page")

        soup = BeautifulSoup(course_details_page.text, "html.parser")
        table = soup.find("table", attrs={"id": "PDGCourse"})
        if table is None:
            raise ScrappingError("Course details table not found")

        data = self.parse_table(table)
        return self.parse_sem_marks(data)

    @staticmethod
    def parse_sem_marks(data: list) -> SemMarkModel:
        CUM_GRADE_X_CREDIT = 0
        CUM_CREDIT = 0
        for d in data[1:]:
            if len(d) >= 7:  # Ensure the row has enough columns
                GRADE = CAMarksWebScrapper.grade_score(d[6])
                try:
                    CREDIT = int(d[7])
                except ValueError:
                    CREDIT = 0
                CUM_GRADE_X_CREDIT += GRADE * CREDIT
                CUM_CREDIT += CREDIT
        
        if CUM_CREDIT == 0:
            return SemMarkModel(latest_sem_no="N/A", latest_sem_cgpa=0)
        
        return SemMarkModel(
            latest_sem_no=data[1][4] if len(data) > 1 and len(data[1]) > 4 else "N/A",
            latest_sem_cgpa=round(CUM_GRADE_X_CREDIT / CUM_CREDIT, 3)
        )

    def fetch_time_table(self) -> List[Dict[str, str]]:
        time_table_page = self.session.get(self.TIMETABLE_PAGE_URL)
        if time_table_page is None or time_table_page.status_code != 200:
            raise ScrappingError(f"Failed to fetch timetable page. Status code: {time_table_page.status_code if time_table_page else 'None'}")
        
        soup = BeautifulSoup(time_table_page.text, "html.parser")
        table = soup.find("table", {"id": "DtStfTimtab"})
        
        if table is None:
            logging.warning("Timetable not found on the page")
            return []
        
        timetable_data = []
        rows = table.find_all("tr")
        
        if len(rows) < 3:  # We need at least the header rows and one day
            logging.warning("Timetable structure is invalid")
            return []
        
        # Extract time slots
        time_slots = [td.text.strip() for td in rows[1].find_all("td")[1:]]
        
        # Process each day
        for row in rows[2:]:  # Start from the third row (first day)
            cols = row.find_all("td")
            if len(cols) < 2:
                continue
            
            day = cols[0].text.strip()
            
            for i, col in enumerate(cols[1:]):
                if i >= len(time_slots):
                    break
                
                time_slot = time_slots[i]
                classes = col.text.strip().split("\n")
                
                if classes and classes[0]:  # If there's a class in this slot
                    for j in range(0, len(classes), 2):
                        if j+1 < len(classes):
                            timetable_data.append({
                                "day": day,
                                "time": time_slot,
                                "programme": classes[j],
                                "course_code": classes[j+1]
                            })
        
        return timetable_data

    def fetch_ca_marks(self):
        ca_marks_page = self.session.get(self.CA_MARKS_URL)
        if ca_marks_page is None or ca_marks_page.status_code != 200:
            raise ScrappingError(f"Failed to fetch CA marks page. Status code: {ca_marks_page.status_code if ca_marks_page else 'None'}")

        soup = BeautifulSoup(ca_marks_page.text, "html.parser")
        table1 = soup.find("table", attrs={"id": "8^1580"})
        table2 = soup.find("table", attrs={"id": "8^1590"})
        
        if table1 is None and table2 is None:
            raise NoCAMarksAvailable

        def parse_table(table):
            data = self.parse_table(table)
            return [
                CAMarksModel(
                    courseCode=row[0],
                    courseTitle=row[1],
                    ca1=row[2] if row[2] != '*' else None,
                    ca2=row[3] if row[3] != '*' else None,
                    ca3=row[4] if row[4] != '*' else None,
                    bestOfCA=row[5] if row[5] != '*' else None,
                    at1=row[6] if row[6] != '*' else None,
                    at2=row[7] if row[7] != '*' else None,
                    ap=row[8] if row[8] != '*' else None,
                    total=row[9] if len(row) > 9 and row[9] != '*' else None
                )
                for row in data[2:]  # Skip header rows
            ]

        ca_marks_1 = parse_table(table1) if table1 else []
        ca_marks_2 = parse_table(table2) if table2 else []

        return ca_marks_1, ca_marks_2

    def fetch_test_timetable(self):
        test_timetable_page = self.session.get(self.TEST_TIME_TABLE_URL)
        if test_timetable_page is None or test_timetable_page.status_code != 200:
            raise ScrappingError(f"Failed to fetch test timetable page. Status code: {test_timetable_page.status_code if test_timetable_page else 'None'}")

        soup = BeautifulSoup(test_timetable_page.text, "html.parser")
        table = soup.find('table', {'id': 'DGTT'})
        
        if table is None:
            logging.warning("Test timetable not found on the page")
            return []
        
        timetable_data = []
        rows = table.find_all('tr')[1:]  # Skip header row
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 6:
                timetable_data.append({
                    'date': cols[0].text.strip(),
                    'day': cols[1].text.strip(),
                    'session': cols[2].text.strip(),
                    'course_code': cols[3].text.strip(),
                    'course_name': cols[4].text.strip(),
                    'room': cols[5].text.strip()
                })
        
        return timetable_data