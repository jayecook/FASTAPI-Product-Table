package com.example.demo;

import org.springframework.stereotype.Service;
import lombok.RequiredArgsConstructor;
import java.util.List;
import java.util.Optional;

//Handles the database operations

@Service
@RequiredArgsConstructor
public class ProductService {
    
    private final ProductRepository productRepository;

    public List<Product> getAll(){
        return productRepository.findAll();
    }

    public Product getById(int id){
        Optional<Product> productToReturn = productRepository.findById(id);
        if(productToReturn.isPresent()){
            return productToReturn.get();
        }
        else{
            return null;
        }
    }

    public void addProduct(Product product){
        productRepository.save(product);
    }

    //Insert function that updates a product based on its here
    //Id is handled on its own, so it shouldn't be updated

    public void deleteById(int id){
        productRepository.deleteById(id);
    }
}
