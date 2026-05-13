class Vacancy:
    def __init__(self, title, link, salary_from, salary_to, currency, description, platform, experience):
        self.title = title
        self.link = link
        self.salary_from = salary_from if salary_from else 0
        self.salary_to = salary_to if salary_to else 0
        self.currency = currency
        self.description = description
        self.platform = platform
        self.experience = experience

        
    def __lt__(self, other):
        self_salary = self.salary_from if self.salary_from else 0
        other_salary = other.salary_from if other.salary_from else 0
        return self_salary < other_salary

    def to_dict(self):
        return {
            'title':self.title,
            'link':self.link,
            'salary_from': self.salary_from,
            'salary_to': self.salary_to,
            'currency': self.currency,
            'description':self.description,
            'platform': self.platform,
            'experience':self.experience
        }