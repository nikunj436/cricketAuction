package com.codelamda.cricketAuction.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.http.HttpStatus;


@Builder
@AllArgsConstructor
@NoArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
@Data
public class ApiResponseDto {

    private Integer statusCode;
    private String message;
    private Object data;
    private boolean success;
    private String status;

    public static ApiResponseDto success(Object data) {
        var response = success();
        response.setData(data);
        return response;
    }

    public static ApiResponseDto success() {
        return ApiResponseDto.builder().success(true).statusCode(HttpStatus.OK.value()).build();
    }

    public static ApiResponseDto failed500() {
        return ApiResponseDto.builder().success(false).statusCode(HttpStatus.INTERNAL_SERVER_ERROR.value()).message(HttpStatus.INTERNAL_SERVER_ERROR.getReasonPhrase()).build();
    }
}