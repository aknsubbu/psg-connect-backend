from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dataFetchFunctions import CAMarksWebScrapper
from dataExceptions import InvalidUsernameOrPasswordException, ScrappingError, NoSemResultsAvailable, NoCAMarksAvailable, AttendanceUpdateInProcessException, NoTimeTableDataException

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class Credentials(BaseModel):
    username: str
    password: str

@app.get("/")
async def root():
    return {"message": "Welcome to the PSG Connect API"}

@app.get("/online")
async def online():
    return {"status": "online"}

@app.post("/fetch_data")
async def fetch_data(credentials: Credentials):
    try:
        scraper = CAMarksWebScrapper(user_name=credentials.username, password=credentials.password)
        
        data = {
            "student_profile": scraper.fetch_student_profile(),
            "attendance": scraper.fetch_attendance(),
            "current_semester_results": scraper.fetch_current_sem_exam_results(),
            "previous_semester_results": scraper.fetch_all_previous_semester_exam_results(),
        }
        
        try:
            ca_marks_1, ca_marks_2 = scraper.fetch_ca_marks()
            data["ca_marks"] = {"CA Marks 1": ca_marks_1, "CA Marks 2": ca_marks_2}
        except NoCAMarksAvailable:
            data["ca_marks"] = "No CA marks available"
        print(data)
        return {"status": "success", "data": data}
    except InvalidUsernameOrPasswordException:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    except AttendanceUpdateInProcessException:
        raise HTTPException(status_code=202, detail="Attendance update is in process")
    except NoSemResultsAvailable:
        raise HTTPException(status_code=404, detail="No semester results available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)