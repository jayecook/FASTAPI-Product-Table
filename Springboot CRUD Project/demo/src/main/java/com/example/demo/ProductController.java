package com.example.demo;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import lombok.RequiredArgsConstructor;
import java.util.List;

//Handles the url mapping

@RestController
@RequiredArgsConstructor
public class ProductController {
    private final ProductService productService;

    @GetMapping("/")
    public ResponseEntity<List<Product>> getAll(){
        return ResponseEntity.ok().body(productService.getAll());
    }

    @GetMapping("/{id}")
    public ResponseEntity<Product> getById(@PathVariable int id){
        return ResponseEntity.ok().body(productService.getById(id));
    }
    
    @PostMapping("/")
    public ResponseEntity<List<Product>> addProduct(@RequestBody Product product) {
        productService.addProduct(product);
        return ResponseEntity.ok().body(productService.getAll());
    }

    //Put the update mapping here

    @DeleteMapping("/{id}")
    public ResponseEntity<List<Product>> deleteById(@PathVariable int id){
        productService.deleteById(id);
        return ResponseEntity.ok().body(productService.getAll());
    }
    
}
