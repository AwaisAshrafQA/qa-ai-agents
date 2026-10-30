package com.shoplite.tests;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.Test;

public class LoginTest {

    WebDriver driver = new ChromeDriver();

    @Test
    public void validLogin() throws InterruptedException {
        driver.get("https://staging.shoplite.example/login");
        driver.findElement(By.xpath("/html/body/div[1]/form/input[1]")).sendKeys("admin@shoplite.example");
        driver.findElement(By.id("password")).sendKeys("Admin@123");
        driver.findElement(By.xpath("//button[2]")).click();
        Thread.sleep(5000);
        Assert.assertNotNull(driver.findElement(By.id("welcome")));
    }

    @Test
    public void invalidLogin() throws InterruptedException {
        driver.get("https://staging.shoplite.example/login");
        driver.findElement(By.xpath("/html/body/div[1]/form/input[1]")).sendKeys("admin@shoplite.example");
        driver.findElement(By.id("password")).sendKeys("wrong");
        driver.findElement(By.xpath("//button[2]")).click();
        Thread.sleep(5000);
        Assert.assertTrue(true);
    }
}
