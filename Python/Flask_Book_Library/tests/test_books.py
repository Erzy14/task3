import unittest
from project import db, app
from project.books.models import Book

class TestBookModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        cls.app = app.test_client()
        with app.app_context():
            db.create_all()

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.drop_all()

    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        db.session.remove()
        self.app_context.pop()

    def test_valid_book(self):
        valid_books = [
            ("The Great Gatsby", "F. Scott Fitzgerald", 1925, "Fiction"),
            ("To Kill a Mockingbird", "Harper Lee", 1960, "Fiction"),
            ("1984", "George Orwell", 1949, "Dystopian"),
            ("Moby Dick", "Herman Melville", 1851, "Adventure"),
            ("War and Peace", "Leo Tolstoy", 1869, "Historical"),
        ]
        for name, author, year, book_type in valid_books:
            book = Book(name=name, author=author, year_published=year, book_type=book_type)
            db.session.add(book)
            db.session.commit()
            retrieved_book = Book.query.filter_by(name=name).first()
            self.assertIsNotNone(retrieved_book)
            self.assertEqual(retrieved_book.name, name)
            self.assertEqual(retrieved_book.author, author)
            self.assertEqual(retrieved_book.year_published, year)
            self.assertEqual(retrieved_book.book_type, book_type)

    def test_invalid_book_missing_data(self):
        invalid_cases = [
            (None, "Author Test", 2020, "Non-Fiction"),
            ("Book Test", None, 2020, "Non-Fiction"),
            ("Book Test", "Author Test", None, "Non-Fiction"),
            ("Book Test", "Author Test", 2020, None),
            ("Book Test", 12345, 2020, "Non-Fiction"),
            (12345, "Author Test", 2020, "Non-Fiction"),
        ]
        for name, author, year, book_type in invalid_cases:
            with self.assertRaises(Exception):
                book = Book(name=name, author=author, year_published=year, book_type=book_type)
                db.session.add(book)
                db.session.commit()

    def test_large_data(self):
        large_lengths = [500, 50000, 5000000]
        for length in large_lengths:
            large_name = "A" * length
            large_author = "B" * length
            with self.assertRaises(Exception):
                book = Book(name=large_name, author=large_author, year_published=2023, book_type="Non-Fiction")
                db.session.add(book)
                db.session.commit()

        large_year = 10**10
        with self.assertRaises(Exception):
            book = Book(name="Large Year", author="Year Test", year_published=large_year, book_type="Fiction")
            db.session.add(book)
            db.session.commit()

    def test_xss_injection(self):
        malicious_payloads = [
            "<script>alert('XSS')</script>",
            "<img src='x' onerror='alert(1)'>",
            "<iframe src='javascript:alert(1)'></iframe>",
            "javascript:alert('XSS')",
            "'; DROP TABLE books; --",
        ]

        for payload in malicious_payloads:
            for field in ['name', 'author', 'book_type']:
                data = {
                    "name": payload if field == "name" else "Valid Name",
                    "author": payload if field == "author" else "Valid Author",
                    "year_published": 2023,
                    "book_type": payload if field == "book_type" else "Valid Type",
                }
                book = Book(**data)
                db.session.add(book)
                db.session.commit()

                retrieved_book = Book.query.filter_by(year_published=2023).first()
                self.assertIsNotNone(retrieved_book)
                self.assertEqual(getattr(retrieved_book, field), payload)
