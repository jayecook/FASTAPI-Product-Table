package com.example.demo;

import org.springframework.data.jpa.repository.JpaRepository;
import com.example.demo.Product;

//This creates the repository

public interface ProductRepository extends JpaRepository<Product, Integer>{
    
}