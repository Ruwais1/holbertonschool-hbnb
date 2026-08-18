```mermaid
erDiagram
    users {
        string id PK
        string first_name
        string last_name
        string email
        string password
        boolean is_admin
        datetime created_at
        datetime updated_at
    }

    place {
        string id PK
        string title
        string description
        float price
        float latitude
        float longitude
        string owner_id FK
        datetime created_at
        datetime updated_at
    }

    review {
        string id PK
        string text
        int rating
        string place_id FK
        string user_id FK
        datetime created_at
        datetime updated_at
    }

    amenity {
        string id PK
        string name
        datetime created_at
        datetime updated_at
    }

    place_amenity {
        string place_id PK, FK
        string amenity_id PK, FK
    }

    users ||--o{ place : owns
    users ||--o{ review : writes
    place ||--o{ review : has
    place ||--|{ place_amenity : contains
    amenity ||--|{ place_amenity : used_in
```
