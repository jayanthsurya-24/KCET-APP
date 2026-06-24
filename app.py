from flask import Flask, render_template, request
import sqlite3
import pandas as pd

app = Flask(__name__)

DB_FILE = "kcet.db"


def get_connection():
    return sqlite3.connect(DB_FILE)


@app.route("/", methods=["GET", "POST"])
def home():

    dream_results = []
    might_results = []
    safe_results = []

    conn = get_connection()

    categories = pd.read_sql_query(
        """
        SELECT DISTINCT Category
        FROM cutoffs
        WHERE Category IS NOT NULL
        ORDER BY Category
        """,
        conn
    )["Category"].tolist()

    courses = pd.read_sql_query(
        """
        SELECT DISTINCT Branch
        FROM cutoffs
        WHERE Branch IS NOT NULL
        ORDER BY Branch
        """,
        conn
    )["Branch"].tolist()

    locations = pd.read_sql_query(
        """
        SELECT DISTINCT Location
        FROM cutoffs
        WHERE Location IS NOT NULL
        ORDER BY Location
        """,
        conn
    )["Location"].tolist()

    if request.method == "POST":

        rank = request.form.get("rank", "").strip()
        category = request.form.get("category", "").strip()

        selected_courses = request.form.getlist("course")
        selected_locations = request.form.getlist("location")

        print("\n===== USER INPUT =====")
        print("Rank:", rank)
        print("Category:", category)
        print("Courses:", selected_courses)
        print("Locations:", selected_locations)

        query = """
        SELECT
            CollegeCode,
            CollegeName,
            Branch,
            Category,
            Rank,
            Location
        FROM cutoffs
        WHERE Rank != '--'
        """

        params = []

        if category:
            query += " AND Category = ? "
            params.append(category)

        if selected_courses:
            placeholders = ",".join(["?"] * len(selected_courses))
            query += f" AND Branch IN ({placeholders}) "
            params.extend(selected_courses)

        if selected_locations:
            placeholders = ",".join(["?"] * len(selected_locations))
            query += f" AND Location IN ({placeholders}) "
            params.extend(selected_locations)

        df = pd.read_sql_query(query, conn, params=params)

        if not df.empty:

            df["Rank"] = pd.to_numeric(df["Rank"], errors="coerce")
            df = df.dropna(subset=["Rank"])

            if rank:

                user_rank = int(rank)

                # Remove duplicate College + Branch combinations
                df = df.drop_duplicates(
                    subset=["CollegeCode", "Branch"]
                )

                # Sort by cutoff rank
                df = df.sort_values("Rank")

                # Dream Colleges
                dream_df = df[
                    (df["Rank"] >= user_rank - 10000)
                    & (df["Rank"] <= user_rank)
                ]

                # Might Get Colleges
                might_df = df[
                    (df["Rank"] > user_rank)
                    & (df["Rank"] <= user_rank + 3000)
                ]

                # Safe Colleges
                safe_df = df[
                    (df["Rank"] > user_rank + 3000)
                ]

                dream_results = dream_df.to_dict(
                    orient="records"
                )

                might_results = might_df.to_dict(
                    orient="records"
                )

                safe_results = safe_df.to_dict(
                    orient="records"
                )

                print("Dream:", len(dream_results))
                print("Might:", len(might_results))
                print("Safe:", len(safe_results))

    conn.close()

    return render_template(
        "index.html",
        categories=categories,
        courses=courses,
        locations=locations,
        dream_results=dream_results,
        might_results=might_results,
        safe_results=safe_results
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    