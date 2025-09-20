package com.codelamda.cricketAuction.entity;
import lombok.Data;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Data
@MappedSuperclass
public class LongIdBaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id", updatable = false, nullable = false)
    private Long id;

    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @PrePersist
    void createDate() {
        if (createdAt == null) {
            setCreatedAt(LocalDateTime.now());
        }
        setUpdatedAt(LocalDateTime.now());
    }

    @PreUpdate
    void updatedAt() {
        setUpdatedAt(LocalDateTime.now());
    }
}
